import * as React from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { FilterScreen } from "./src/screens/FilterScreen";
import { SwipeScreen } from "./src/screens/SwipeScreen";
import { MatchScreen } from "./src/screens/MatchScreen";
import { colors } from "./src/theme/colors";

export type RootStackParamList = {
  Filters: undefined;
  Swipe: undefined;
  Match: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        initialRouteName="Filters"
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="Filters" component={FilterScreen} />
        <Stack.Screen name="Swipe" component={SwipeScreen} />
        <Stack.Screen name="Match" component={MatchScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
