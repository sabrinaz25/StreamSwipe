import * as React from "react";
import { Pressable, Text, StyleSheet, ViewStyle } from "react-native";

import { colors } from "../theme/colors";

export function Button({
  label,
  onPress,
  variant = "primary",
  style,
  disabled,
}: {
  label: string;
  onPress: () => void;
  variant?: "primary" | "danger" | "ghost";
  style?: ViewStyle;
  disabled?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.base,
        variant === "primary" && styles.primary,
        variant === "danger" && styles.danger,
        variant === "ghost" && styles.ghost,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
        style,
      ]}
    >
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.border,
  },
  primary: { backgroundColor: colors.primary },
  danger: { backgroundColor: colors.danger },
  ghost: { backgroundColor: "transparent" },
  label: { color: colors.text, fontWeight: "700", letterSpacing: 0.2 },
  pressed: { transform: [{ scale: 0.98 }] },
  disabled: { opacity: 0.5 },
});

