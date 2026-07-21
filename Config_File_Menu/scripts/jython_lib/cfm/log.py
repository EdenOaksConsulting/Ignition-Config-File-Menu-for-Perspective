"""Named-logger observability with de-duplication (flood-safe).

Runtime handlers fire on every render / navigation / binding evaluation, so the
deployed runtime is deliberately quiet. These helpers surface *genuine* faults to
the gateway logs under a stable ``CFM.*`` logger prefix WITHOUT reintroducing
floods:

  * high-frequency callers use ``log_once`` (de-duplicated per area+message),
  * low-frequency user-triggered callers use ``log_always``.

Logging can never raise into a handler (every path is wrapped in try/except).

Adjust verbosity at runtime in Gateway -> Status -> Diagnostics -> Logs (loggers
named ``CFM`` and ``CFM.<area>``; changes persist to wrapper.log). The ``[CFM ...]``
message markers written by callers are stable for alert scraping.
"""

# Bounded module-level de-dup cache. The gateway interpreter is long-lived, so the
# cache is capped and cleared wholesale when it fills — it cannot grow without limit.
_LOG_ONCE_CACHE = {}
_LOG_ONCE_CACHE_CAP = 200

_LEVELS = ("error", "warn", "info", "debug")


def get_logger(name=""):
	# Stable CFM.* logger name. Every review/alert mechanism keys off this prefix.
	suffix = "." + name if name else ""
	return system.util.getLogger("CFM" + suffix)


def _should_emit(cache, key, message):
	# Pure, unit-testable de-dup core. Emit when this key has not been seen, or when
	# its stored message changed. Bounds the cache: clear it wholesale once it reaches
	# the cap so a long-lived interpreter cannot grow it without limit.
	if cache.get(key) == message:
		return False
	if len(cache) >= _LOG_ONCE_CACHE_CAP:
		cache.clear()
	cache[key] = message
	return True


def _emit(area, level, message, exc):
	lvl = str(level or "info").lower()
	if lvl not in _LEVELS:
		lvl = "info"
	text = message
	if exc is not None:
		# Do not assume a Java Throwable; str() works for Jython and Python exceptions.
		text = text + ": " + str(exc)
	logger = get_logger(area)
	if lvl == "error":
		logger.error(text)
	elif lvl == "warn":
		logger.warn(text)
	elif lvl == "debug":
		logger.debug(text)
		if exc is not None:
			try:
				import traceback
				logger.debug(traceback.format_exc())
			except:
				pass
	else:
		logger.info(text)


def log_always(area, level, message, exc=None):
	# Log every time (no de-dup). For low-frequency, user-triggered paths (Settings
	# actions), where each occurrence is worth a line.
	try:
		_emit(area, level, message, exc)
	except:
		pass


def log_once(area, level, message, exc=None):
	# Log only when this (area, message) has not been seen (or its message changed).
	# For high-frequency render / navigation / binding paths, so a repeating fault
	# produces one line rather than a flood.
	try:
		key = str(area) + "|" + str(message)
		if _should_emit(_LOG_ONCE_CACHE, key, message):
			_emit(area, level, message, exc)
	except:
		pass


# --- Performance logging (opt-in, zero-overhead when off) -------------------
#
# Timing/formatting must never run on a hot path unless perf logging is actually
# enabled, so callers GATE with ``perf_enabled(...)`` BEFORE they call ``now_nanos``
# or build the ``extra`` string:
#
#     perf_prop = cfm.config.is_true(state.get("perfLogging", False))
#     _perf = cfm.log.perf_enabled(perf_prop)
#     _t0 = cfm.log.now_nanos() if _perf else 0
#     ... work ...
#     if _perf:
#         cfm.log.perf("breadcrumb.build", cfm.log.now_nanos() - _t0,
#             "items=%d" % len(items), force=perf_prop)
#
# Two independent gates: the ``CFM.perf`` logger's TRACE level (Gateway -> Status ->
# Diagnostics -> Logs) and the resolved ``perfLogging`` session property (passed in as
# ``force`` so operators can toggle it from the app without gateway access). ``log.py``
# stays free of a ``config`` dependency: the caller resolves ``perfLogging`` from state
# it already read, so no extra session read happens on a hot path. The ``[CFM perf]``
# marker is stable for alert scraping (matching ``[CFM ...]`` / ``[CFM health]``).


def now_nanos():
	# Monotonic-ish nanosecond counter. Uses java.lang.System.nanoTime() under Jython
	# and falls back to the wall clock under CPython (tests). Never raises.
	try:
		from java.lang import System as _JavaSystem
		return _JavaSystem.nanoTime()
	except:
		try:
			import time
			return int(time.time() * 1000000000.0)
		except:
			return 0


def perf_enabled(perf_prop=False):
	# True when perf logging should run: either the caller-resolved perfLogging property
	# is on, or the CFM.perf logger has TRACE enabled. Wrapped so a broken logger can never
	# make a hot path throw; defaults to False (off) on any error.
	try:
		return bool(perf_prop) or bool(get_logger("perf").isTraceEnabled())
	except:
		return False


def perf(label, nanos, extra="", threshold_ms=0, force=False):
	# Emit one timing line under the CFM.perf logger. Callers must already have gated the
	# measurement with perf_enabled(); this re-checks so a stray call is still cheap/safe.
	# threshold_ms > 0 suppresses fast cases (surface only slow ones). When forced (the
	# perfLogging property is on) it logs at INFO so it is visible at default gateway
	# levels; otherwise it logs at TRACE. Never raises into a handler.
	try:
		logger = get_logger("perf")
		trace_on = logger.isTraceEnabled()
		if not (force or trace_on):
			return
		ms = nanos / 1000000.0
		if threshold_ms and ms < threshold_ms:
			return
		msg = "[CFM perf] " + str(label) + " " + ("%.1f" % ms) + "ms"
		if extra:
			msg = msg + " " + str(extra)
		if force:
			logger.info(msg)
		else:
			logger.trace(msg)
	except:
		pass
