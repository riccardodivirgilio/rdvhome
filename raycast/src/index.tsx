import { ActionPanel, Action, List, Icon, Color } from "@raycast/api";
import { useFetch } from "@raycast/utils";
import { showToast, Toast } from "@raycast/api";

import { useState, useEffect } from "react";

//https://github.com/raycast/extensions/blob/main/examples/todo-list/src/index.tsx

function hue_to_rgb(h, s = 1, v = 1) {
  let r, g, b, i, f, p, q, t;

  i = Math.floor(h * 6);
  f = h * 6 - i;
  p = v * (1 - s);
  q = v * (1 - f * s);
  t = v * (1 - (1 - f) * s);
  switch (i % 6) {
    case 0:
      (r = v), (g = t), (b = p);
      break;
    case 1:
      (r = q), (g = v), (b = p);
      break;
    case 2:
      (r = p), (g = v), (b = t);
      break;
    case 3:
      (r = p), (g = q), (b = v);
      break;
    case 4:
      (r = t), (g = p), (b = v);
      break;
    case 5:
      (r = v), (g = p), (b = q);
      break;
  }

  r = Math.round(r * 255);
  g = Math.round(g * 255);
  b = Math.round(b * 255);

  return `rgb(${r}, ${g}, ${b})`;
}

function get_api(path) {
  return "http://rdvhome.local:8500/" + path;
}

/** Parse the response from the fetch query into something we can display */
async function updateState(setToggles) {
  const json = await (await fetch(get_api("switch"))).json();

  if ("reason" in json) {
    throw new Error(json.reason);
  }

  await setToggles(Object.values(json.switches || []).filter((toggle) => toggle.allow_visibility));
}

const is_on = (t) => t.kind == "switch" && t.allow_on && t.on;
const is_off = (t) => t.kind == "switch" && t.allow_on && !t.on;
const is_windows = (t) => t.kind == "switch" && t.allow_direction;
const is_controls = (t) => t.kind != "switch";

export default function Command() {
  const [toggles, setToggles] = useState([]);

  useEffect(() => updateState(setToggles), []); // Or [] if effect doesn't need props or state

  const on = toggles.filter(is_on);
  const off = toggles.filter(is_off);
  const windows = toggles.filter(is_windows);
  const controls = toggles.filter(is_controls);

  return (
    <List isLoading={toggles.length == 0} searchBarPlaceholder="Search lights...">
      <List.Section title="On" subtitle={on.length}>
        {on.map((toggle) => (
          <SearchListItem key={toggle.name} toggle={toggle} setToggles={setToggles} />
        ))}
      </List.Section>
      <List.Section title="Off" subtitle={off.length}>
        {off.map((toggle) => (
          <SearchListItem key={toggle.name} toggle={toggle} setToggles={setToggles} />
        ))}
      </List.Section>
      <List.Section title="Windows" subtitle={controls.length}>
        {windows.map((toggle) => (
          <SearchListItem key={toggle.name} toggle={toggle} setToggles={setToggles} />
        ))}
      </List.Section>
      <List.Section title="Controls" subtitle={controls.length}>
        {controls.map((toggle) => (
          <SearchListItem key={toggle.name} toggle={toggle} setToggles={setToggles} />
        ))}
      </List.Section>
    </List>
  );
}

export async function run_api(endpoint, message, setToggles) {
  const toast = await showToast({
    style: Toast.Style.Animated,
    title: message,
  });

  await fetch(get_api(endpoint));
  await updateState(setToggles);

  await toast.hide();
}

function ToggleAction({ endpoint, message, title, setToggles, icon, shortcut }) {
  return (
    <Action
      title={title || message}
      onAction={() => run_api(endpoint, message || title, setToggles)}
      icon={icon}
      shortcut={shortcut}
    />
  );
}

function* GenerateToggleCapabilities({ toggle, setToggles }) {
  if (toggle.allow_on) {
    yield (
      <ActionPanel.Section>
        <ToggleAction
          message={`Switch ${toggle.name} ${toggle.on ? "off" : "on"}`}
          endpoint={`switch/${toggle.id}/${toggle.on ? "off" : "on"}`}
          setToggles={setToggles}
        />
      </ActionPanel.Section>
    );
  }

  if (toggle.allow_direction) {
    yield (
      <ActionPanel.Section>
        <ToggleAction
          title="Up"
          message={`Switch ${toggle.name} Up`}
          endpoint={`switch/${toggle.id}/up`}
          setToggles={setToggles}
          icon={Icon.ArrowUpCircle}
          shortcut={{ modifiers: ["cmd", "shift"], key: "arrowUp" }}
        />
        <ToggleAction
          title="Stop"
          message={`Switch ${toggle.name} stop`}
          endpoint={`switch/${toggle.id}/stop`}
          setToggles={setToggles}
          icon={Icon.Stop}
          shortcut={{ modifiers: ["cmd", "shift"], key: "enter" }}
        />
        <ToggleAction
          title="Down"
          message={`Switch ${toggle.name} Down`}
          endpoint={`switch/${toggle.id}/down`}
          setToggles={setToggles}
          icon={Icon.ArrowDownCircle}
          shortcut={{ modifiers: ["cmd", "shift"], key: "arrowDown" }}
        />
      </ActionPanel.Section>
    );
  }

  if (toggle.allow_hue) {
    yield (
      <ActionPanel.Section title="Change color">
        {[
          [Math.random(), "Random", "r"],
          [1, "Red", "1"],
          [0.857143, "Purple", "2"],
          [0.714286, "Blue", "3"],
          [0.571429, "Celeste", "4"],
          [0.428571, "Slate green", "5"],
          [0.285714, "Green", "6"],
          [0.142857, "Yellow", "7"],
        ].map(([h, name, key]) => (
          <ToggleAction
            title={name}
            message={`Switch ${toggle.name} ${name}`}
            endpoint={`switch/${toggle.id}/on/${Math.round(h * 100)}/100/-`}
            setToggles={setToggles}
            icon={{
              source: Icon.CircleProgress100,
              tintColor: hue_to_rgb(h),
            }}
            shortcut={{ modifiers: ["cmd", "shift"], key: key }}
          />
        ))}
      </ActionPanel.Section>
    );
  }
}

function get_icon(toggle) {
  if (toggle.up) {
    return Icon.ArrowUpCircle;
  }
  if (toggle.down) {
    return Icon.ArrowDownCircle;
  }
  if (toggle.allow_direction) {
    return Icon.Stop;
  }

  if (toggle.on) {
    return Icon.CircleProgress100;
  }
  return Icon.Circle;
}

function SearchListItem({ toggle, setToggles }) {
  return (
    <List.Item
      id={toggle.id}
      title={toggle.name}
      subtitle={toggle.icon}
      accessories={toggle.alias.map((a) => ({ text: a }))}
      icon={{
        source: get_icon(toggle),
        tintColor: toggle.on && toggle.hue ? hue_to_rgb(toggle.hue) : null,
      }}
      actions={<ActionPanel>{[...GenerateToggleCapabilities({ toggle, setToggles })]}</ActionPanel>}
    />
  );
}
