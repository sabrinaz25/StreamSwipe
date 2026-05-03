import * as React from "react";
import { Dimensions, Image, StyleSheet, Text, View } from "react-native";

import type { FeedItem } from "../api/types";
import { colors } from "../theme/colors";

const { height: SCREEN_HEIGHT, width: SCREEN_WIDTH } = Dimensions.get("window");

export function Card({ item }: { item: FeedItem }) {
  return (
    <View style={styles.card}>
      {item.poster_url ? (
        <Image source={{ uri: item.poster_url }} style={styles.poster} resizeMode="cover" />
      ) : (
        <View style={styles.posterFallback}>
          <Text style={styles.posterFallbackText}>{item.title.slice(0, 1).toUpperCase()}</Text>
        </View>
      )}
      <View style={styles.body}>
        <Text style={styles.title}>{item.title}</Text>
        {!!item.genres?.length && (
          <Text style={styles.meta}>{item.genres.slice(0, 3).join(" • ")}</Text>
        )}
        <Text style={styles.overview} numberOfLines={6}>
          {item.overview || "No synopsis available."}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 20,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.border,
    maxHeight: SCREEN_HEIGHT * 0.72,
    width: SCREEN_WIDTH > 600 ? 380 : "95%",
    alignSelf: "center",
},
  poster: { width: "100%", height: SCREEN_HEIGHT * 0.52, backgroundColor: "#0f1423" },
  posterFallback: {
    width: "100%",
    height: SCREEN_HEIGHT * 0.52,
    backgroundColor: "#0f1423",
    alignItems: "center",
    justifyContent: "center",
},
  posterFallbackText: { color: colors.text, fontSize: 48, fontWeight: "900" },
  body: { padding: 14, gap: 6 },
  title: { color: colors.text, fontSize: 20, fontWeight: "800" },
  meta: { color: colors.muted, fontSize: 13 },
  overview: { color: colors.text, opacity: 0.9, lineHeight: 20 },
});

