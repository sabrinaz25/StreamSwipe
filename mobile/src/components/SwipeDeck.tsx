import * as React from "react";
import {
  Animated,
  Dimensions,
  PanResponder,
  StyleSheet,
  View,
  type PanResponderGestureState,
} from "react-native";

import type { FeedItem, SwipeDirection } from "../api/types";
import { Card } from "./Card";

const SWIPE_THRESHOLD_PX = 110;

function swipeDirectionFromDx(dx: number): SwipeDirection | null {
  if (dx > SWIPE_THRESHOLD_PX) return "right";
  if (dx < -SWIPE_THRESHOLD_PX) return "left";
  return null;
}

export function SwipeDeck({
  item,
  disabled,
  onSwipe,
}: {
  item: FeedItem;
  disabled?: boolean;
  onSwipe: (direction: SwipeDirection, item: FeedItem) => void | Promise<void>;
}) {
  const position = React.useRef(new Animated.ValueXY()).current;
  const isAnimatingRef = React.useRef(false);

  const width = Dimensions.get("window").width;
  const offscreenX = Math.max(width * 1.2, 500);

  const rotate = position.x.interpolate({
    inputRange: [-offscreenX, 0, offscreenX],
    outputRange: ["-10deg", "0deg", "10deg"],
    extrapolate: "clamp",
  });

  const likeOpacity = position.x.interpolate({
    inputRange: [0, SWIPE_THRESHOLD_PX],
    outputRange: [0, 1],
    extrapolate: "clamp",
  });
  const nopeOpacity = position.x.interpolate({
    inputRange: [-SWIPE_THRESHOLD_PX, 0],
    outputRange: [1, 0],
    extrapolate: "clamp",
  });

  const reset = React.useCallback(() => {
    position.setValue({ x: 0, y: 0 });
  }, [position]);

  const animateOffscreen = React.useCallback(
    (dir: SwipeDirection, gesture: PanResponderGestureState) => {
      if (isAnimatingRef.current) return;
      isAnimatingRef.current = true;

      const toX = dir === "right" ? offscreenX : -offscreenX;
      Animated.timing(position, {
        toValue: { x: toX, y: gesture.dy * 0.2 },
        duration: 220,
        useNativeDriver: false, // works on web too
      }).start(async () => {
        try {
          await onSwipe(dir, item);
        } finally {
          reset();
          isAnimatingRef.current = false;
        }
      });
    },
    [item, offscreenX, onSwipe, position, reset]
  );

  const panResponder = React.useMemo(
    () =>
      PanResponder.create({
        onMoveShouldSetPanResponder: (_evt, g) => {
          if (disabled) return false;
          if (isAnimatingRef.current) return false;
          return Math.abs(g.dx) > 6 || Math.abs(g.dy) > 6;
        },
        onPanResponderMove: (_evt, g) => {
          position.setValue({ x: g.dx, y: g.dy });
        },
        onPanResponderRelease: (_evt, g) => {
          const dir = swipeDirectionFromDx(g.dx);
          if (dir) {
            animateOffscreen(dir, g);
            return;
          }
          Animated.spring(position, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: false,
            friction: 7,
            tension: 60,
          }).start();
        },
        onPanResponderTerminate: () => {
          Animated.spring(position, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: false,
            friction: 7,
            tension: 60,
          }).start();
        },
      }),
    [animateOffscreen, disabled, position]
  );

  return (
    <View style={styles.root}>
      <Animated.View style={[styles.badge, styles.nope, { opacity: nopeOpacity }]}>
        <Animated.Text style={styles.badgeText}>NOPE</Animated.Text>
      </Animated.View>
      <Animated.View style={[styles.badge, styles.like, { opacity: likeOpacity }]}>
        <Animated.Text style={styles.badgeText}>LIKE</Animated.Text>
      </Animated.View>

      <Animated.View
        {...panResponder.panHandlers}
        style={[
          {
            transform: [{ translateX: position.x }, { translateY: position.y }, { rotate }],
          },
        ]}
      >
        <Card item={item} />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { width: "100%", alignSelf: "center" },
  badge: {
    position: "absolute",
    top: 18,
    zIndex: 5,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderWidth: 2,
    borderRadius: 10,
    backgroundColor: "rgba(0,0,0,0.15)",
  },
  badgeText: { fontWeight: "900", letterSpacing: 1.2, fontSize: 14, color: "#fff" },
  like: { right: 18, borderColor: "#2EE59D" },
  nope: { left: 18, borderColor: "#FF4D6D" },
});

