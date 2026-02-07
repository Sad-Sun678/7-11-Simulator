"""Lightweight tween / animation utilities for the scratch-card game."""


class Tween:
    """Animates a single float value from *start* to *end* over *duration* seconds
    using a pluggable easing function.

    Usage::

        tw = Tween(0, 100, 0.5, ease_func="ease_out_quad")
        while not tw.done:
            tw.update(dt)
            x = tw.get_value()
    """

    EASE_FUNCS = {}  # populated by _register helpers below

    def __init__(self, start, end, duration, ease_func="ease_out_quad"):
        self.start = float(start)
        self.end = float(end)
        self.duration = max(duration, 0.001)  # avoid /0
        self.elapsed = 0.0
        self.done = False
        self._value = float(start)

        if callable(ease_func):
            self._ease = ease_func
        else:
            self._ease = self.EASE_FUNCS.get(ease_func, Tween.ease_out_quad)

    def update(self, dt):
        """Advance the tween. Returns True when the tween has finished."""
        if self.done:
            return True
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)
        eased = self._ease(t)
        self._value = self.start + (self.end - self.start) * eased
        if t >= 1.0:
            self._value = self.end
            self.done = True
        return self.done

    def get_value(self):
        return self._value

    # ----- built-in easing functions -----

    @staticmethod
    def ease_linear(t):
        return t

    @staticmethod
    def ease_out_quad(t):
        return 1 - (1 - t) ** 2

    @staticmethod
    def ease_in_quad(t):
        return t * t

    @staticmethod
    def ease_out_back(t):
        """Slight overshoot — nice for deal animations."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    @staticmethod
    def ease_out_cubic(t):
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out_quad(t):
        if t < 0.5:
            return 2 * t * t
        return 1 - (-2 * t + 2) ** 2 / 2


# Register all built-in easing functions
Tween.EASE_FUNCS = {
    "linear": Tween.ease_linear,
    "ease_out_quad": Tween.ease_out_quad,
    "ease_in_quad": Tween.ease_in_quad,
    "ease_out_back": Tween.ease_out_back,
    "ease_out_cubic": Tween.ease_out_cubic,
    "ease_in_out_quad": Tween.ease_in_out_quad,
}


class TweenGroup:
    """Runs multiple Tweens in parallel (e.g. x and y for a 2-D slide)."""

    def __init__(self, tweens):
        """tweens: dict of name -> Tween, e.g. {"x": Tween(...), "y": Tween(...)}"""
        self.tweens = tweens
        self.done = False

    def update(self, dt):
        all_done = True
        for tw in self.tweens.values():
            tw.update(dt)
            if not tw.done:
                all_done = False
        self.done = all_done
        return self.done

    def get_values(self):
        """Return dict of name -> current value."""
        return {name: tw.get_value() for name, tw in self.tweens.items()}


class AnimationManager:
    """Owns a list of active animations (Tween or TweenGroup),
    updates them each frame, fires callbacks on completion, and
    removes finished animations.

    Usage::

        mgr = AnimationManager()
        mgr.add(my_tween, on_complete=lambda: print("done"))
        # each frame:
        mgr.update(dt)
    """

    def __init__(self):
        self._entries = []  # list of (tween_or_group, callback, tag)

    def add(self, tween, callback=None, tag=None):
        """Add a Tween or TweenGroup. *callback* is called (no args) when it
        finishes. *tag* is an optional string used by ``cancel(tag)``."""
        self._entries.append((tween, callback, tag))

    def update(self, dt):
        still_alive = []
        for tween, callback, tag in self._entries:
            done = tween.update(dt)
            if done:
                if callback:
                    callback()
            else:
                still_alive.append((tween, callback, tag))
        self._entries = still_alive

    def cancel(self, tag):
        """Remove all entries with the given tag (without calling callbacks)."""
        self._entries = [(t, cb, tg) for t, cb, tg in self._entries if tg != tag]

    def cancel_all(self):
        self._entries.clear()

    def is_animating(self, tag=None):
        """True if any animation (optionally filtered by tag) is running."""
        if tag is None:
            return len(self._entries) > 0
        return any(tg == tag for _, _, tg in self._entries)
