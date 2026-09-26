from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import sleep
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

import requests


URL_BASE = "https://www.dnd5eapi.co/api/2014/"
SUPPORTED_COLLECTIONS = {
	"monsters": "monster",
	"spells": "spell",
	"classes": "class",
	"races": "race",
	"backgrounds": "background",
	"feats": "feat",
	"equipment": "item",
	"subclasses": "subclass",
}
QUERY_OPTIONS = {
	"monsters": ("challenge_rating",),
	"spells": ("level", "school"),
	"equipment": ("category",),
}
MAX_REQUEST_RETRIES = 5
MAX_RESOURCE_WORKERS = 4
MAX_FEATURE_WORKERS = 4


class SRDClient:
	"""Small client for collection and detail requests to the 5eSRD API."""

	def __init__(self, session: requests.Session | None = None, base_url=URL_BASE):
		self.session = session or requests.Session()
		self.base_url = base_url.rstrip("/") + "/"
		self._response_cache = {}
		self._cache_lock = Lock()

	def collections(self) -> tuple[str, ...]:
		response = self._get("")
		available = set(response)
		return tuple(
			collection for collection in SUPPORTED_COLLECTIONS if collection in available
		)

	def query_options(self, collection: str) -> tuple[str, ...]:
		return QUERY_OPTIONS.get(collection, ())

	def fetch_collection(
		self,
		collection: str,
		*,
		query: Mapping[str, str] | None = None,
		include_details: bool = True,
	) -> list[dict[str, Any]]:
		if collection not in SUPPORTED_COLLECTIONS:
			raise ValueError(f"Unsupported 5eSRD collection: {collection}")
		document = self._get(collection, params=clean_query(query))
		results = document.get("results", [])
		if not include_details:
			return list(results)
		details = [self._get(item["url"]) for item in results if item.get("url")]
		for detail in details:
			self._expand_related(detail)
			if collection in {"classes", "subclasses"}:
				self._hydrate_levels(
					detail,
					"class_levels" if collection == "classes" else "subclass_levels",
				)
			if collection == "races":
				self._hydrate_references(detail, "traits")
		return details

	def fetch_collection_resources(
		self,
		collection: str,
		*,
		query: Mapping[str, str] | None = None,
		is_cancelled: Callable[[], bool] | None = None,
		progress_callback: Callable[[int, int], None] | None = None,
	) -> list[dict[str, Any]]:
		"""Fetch every supported entity reachable from a collection.

		Each result includes its API collection, hydrated payload, and the
		resource that contained its URL reference.
		"""
		if collection not in SUPPORTED_COLLECTIONS:
			raise ValueError(f"Unsupported 5eSRD collection: {collection}")
		document = self._get(collection, params=clean_query(query))
		resources = []
		visited: set[str] = set()
		visited_lock = Lock()
		resources_lock = Lock()
		progress_lock = Lock()
		progress = {"current": 0, "total": len(document.get("results", []))}
		endpoints = [
			item["url"]
			for item in document.get("results", [])
			if isinstance(item, dict) and item.get("url")
		]
		with ThreadPoolExecutor(max_workers=MAX_RESOURCE_WORKERS) as executor:
			futures = [
				executor.submit(
					self._collect_resource,
					endpoint,
					collection,
					None,
					visited,
					resources,
					is_cancelled=is_cancelled,
					progress_callback=progress_callback,
					progress=progress,
					visited_lock=visited_lock,
					resources_lock=resources_lock,
					progress_lock=progress_lock,
				)
				for endpoint in endpoints
			]
			for future in futures:
				future.result()
		return resources

	def _collect_resource(
		self,
		endpoint: str,
		collection: str,
		parent: dict[str, Any] | None,
		visited: set[str],
		resources: list[dict[str, Any]],
		*,
		is_cancelled: Callable[[], bool] | None = None,
		progress_callback: Callable[[int, int], None] | None = None,
		progress: dict[str, int] | None = None,
		visited_lock: Lock | None = None,
		resources_lock: Lock | None = None,
		progress_lock: Lock | None = None,
		reference: dict[str, Any] | None = None,
	):
		if is_cancelled is not None and is_cancelled():
			return
		url = absolute_url(endpoint, self.base_url)
		if visited_lock is None:
			if url in visited:
				return
			visited.add(url)
		else:
			with visited_lock:
				if url in visited:
					return
				visited.add(url)
		payload = self._get(url)
		if reference is not None:
			reference.clear()
			reference.update(payload)
		actual_collection = collection_from_url(url, self.base_url) or collection
		if actual_collection in {"classes", "subclasses"} and "/levels" not in urlparse(url).path:
			self._hydrate_levels(payload, "class_levels" if actual_collection == "classes" else "subclass_levels")
		if actual_collection == "races":
			self._hydrate_references(payload, "traits")
		if progress is not None:
			if progress_lock is None:
				progress["current"] += 1
				progress["total"] = max(progress["total"], progress["current"])
				current, total = progress["current"], progress["total"]
			else:
				with progress_lock:
					progress["current"] += 1
					progress["total"] = max(progress["total"], progress["current"])
					current, total = progress["current"], progress["total"]
			if progress_callback is not None:
				progress_callback(current, total)
		resource = {
			"collection": actual_collection,
			"payload": payload,
			"parent": parent,
		}
		if actual_collection in SUPPORTED_COLLECTIONS:
			if resources_lock is None:
				resources.append(resource)
			else:
				with resources_lock:
					resources.append(resource)
		self._collect_nested_resources(
			payload,
			actual_collection,
			visited,
			resources,
			is_cancelled=is_cancelled,
			progress_callback=progress_callback,
			progress=progress,
			visited_lock=visited_lock,
			resources_lock=resources_lock,
			progress_lock=progress_lock,
		)

	def _hydrate_levels(self, payload: dict[str, Any], key: str):
		endpoint = payload.get(key)
		if not isinstance(endpoint, str):
			return
		levels = self._get(endpoint)
		if not isinstance(levels, list):
			return
		feature_urls = [
				feature["url"]
				for level in levels
				for feature in level.get("features", [])
				if isinstance(feature, dict) and feature.get("url")
		]
		with ThreadPoolExecutor(max_workers=MAX_FEATURE_WORKERS) as executor:
			feature_payloads = dict(
				zip(feature_urls, executor.map(self._get, feature_urls), strict=False)
			)
		for level in levels:
			for feature in level.get("features", []):
				if isinstance(feature, dict) and feature.get("url"):
					feature_payload = feature_payloads[feature["url"]]
					feature.clear()
					feature.update(feature_payload)
		payload[key] = levels

	def _hydrate_references(self, payload: dict[str, Any], key: str):
		references = payload.get(key)
		if not isinstance(references, list):
			return
		urls = [
			item.get("url")
			for item in references
			if isinstance(item, dict) and isinstance(item.get("url"), str)
		]
		if not urls:
			return
		with ThreadPoolExecutor(max_workers=MAX_FEATURE_WORKERS) as executor:
			values = dict(zip(urls, executor.map(self._get, urls), strict=False))
		for item in references:
			url = item.get("url") if isinstance(item, dict) else None
			if url in values:
				item.clear()
				item.update(values[url])

	def _collect_nested_resources(
		self,
		value: Any,
		parent_collection: str,
		visited: set[str],
		resources: list[dict[str, Any]],
		*,
		is_cancelled: Callable[[], bool] | None = None,
		progress_callback: Callable[[int, int], None] | None = None,
		progress: dict[str, int] | None = None,
		visited_lock: Lock | None = None,
		resources_lock: Lock | None = None,
		progress_lock: Lock | None = None,
	):
		if is_cancelled is not None and is_cancelled():
			return
		if isinstance(value, list):
			for item in value:
				self._collect_nested_resources(
					item,
					parent_collection,
					visited,
					resources,
					is_cancelled=is_cancelled,
					progress_callback=progress_callback,
					progress=progress,
					visited_lock=visited_lock,
					resources_lock=resources_lock,
					progress_lock=progress_lock,
				)
			return
		if not isinstance(value, dict):
			return
		for child in value.values():
			if isinstance(child, dict) and isinstance(child.get("url"), str):
				child_url = absolute_url(child["url"], self.base_url)
				child_collection = collection_from_url(child_url, self.base_url)
				self._collect_resource(
					child_url,
					child_collection or parent_collection,
					value,
					visited,
					resources,
					is_cancelled=is_cancelled,
					progress_callback=progress_callback,
					progress=progress,
					visited_lock=visited_lock,
					resources_lock=resources_lock,
					progress_lock=progress_lock,
					reference=child,
				)
			else:
				self._collect_nested_resources(
					child,
					parent_collection,
					visited,
					resources,
					is_cancelled=is_cancelled,
					progress_callback=progress_callback,
					progress=progress,
					visited_lock=visited_lock,
					resources_lock=resources_lock,
					progress_lock=progress_lock,
				)

	def _expand_related(self, value: Any):
		if isinstance(value, list):
			for item in value:
				self._expand_related(item)
			return
		if not isinstance(value, dict):
			return
		endpoint = value.get("url")
		if isinstance(endpoint, str) and "/subclasses/" in urlparse(endpoint).path:
			value.clear()
			value.update(self._get(endpoint))
			return
		for child in value.values():
			self._expand_related(child)

	def _get(self, endpoint: str, *, params=None):
		url = absolute_url(endpoint, self.base_url)
		cache_key = (url, tuple(sorted((params or {}).items())))
		with self._cache_lock:
			if cache_key in self._response_cache:
				return deepcopy(self._response_cache[cache_key])
		for attempt in range(MAX_REQUEST_RETRIES + 1):
			response = self.session.get(
				url,
				params=params,
				headers={
					"Accept": "application/json",
					"User-Agent": "DMTools-SRD-Importer/1.0",
				},
				timeout=30,
			)
			if response.status_code != 429 or attempt >= MAX_REQUEST_RETRIES:
				response.raise_for_status()
				break
			retry_after = response.headers.get("Retry-After")
			try:
				delay = float(retry_after)
			except (TypeError, ValueError):
				delay = 2 ** attempt
			sleep(min(max(delay, 0.5), 30))
		payload = response.json()
		with self._cache_lock:
			self._response_cache[cache_key] = payload
		return deepcopy(payload)


def absolute_url(endpoint: str, base_url: str = URL_BASE) -> str:
	if endpoint.startswith("http"):
		return endpoint
	if endpoint.startswith("/"):
		parsed = urlparse(base_url)
		origin = f"{parsed.scheme}://{parsed.netloc}"
		return urljoin(origin, endpoint)
	return urljoin(base_url, endpoint)


def collection_from_url(url: str, base_url: str = URL_BASE) -> str | None:
	relative = url.removeprefix(base_url).strip("/")
	parts = relative.split("/")
	return parts[0] if parts and parts[0] else None


def clean_query(query: Mapping[str, str] | None) -> dict[str, str]:
	if not query:
		return {}
	return {key: str(value).strip() for key, value in query.items() if str(value).strip()}
