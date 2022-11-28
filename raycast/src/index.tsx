import { ActionPanel, Action, List, Icon, Color } from "@raycast/api";
import { useFetch } from "@raycast/utils";
import { showToast, Toast } from "@raycast/api";

import { useState, useEffect } from "react";

//https://github.com/raycast/extensions/blob/main/examples/todo-list/src/index.tsx


function hue_to_rgb(h, s = 1, v=1) {
    var r, g, b, i, f, p, q, t;

    i = Math.floor(h * 6);
    f = h * 6 - i;
    p = v * (1 - s);
    q = v * (1 - f * s);
    t = v * (1 - (1 - f) * s);
    switch (i % 6) {
        case 0: r = v, g = t, b = p; break;
        case 1: r = q, g = v, b = p; break;
        case 2: r = p, g = v, b = t; break;
        case 3: r = p, g = q, b = v; break;
        case 4: r = t, g = p, b = v; break;
        case 5: r = v, g = p, b = q; break;
    }

    r = Math.round(r * 255)
    g = Math.round(g * 255)
    b = Math.round(b * 255)

    return `rgb(${r}, ${g}, ${b})`

}

export async function run_toggle(toggle, setToggles) {
  const toast = await showToast({
    style: Toast.Style.Animated,
    title: `Switched ${toggle.on ? "off" : "on"} ${toggle.name}`,
  });

  await fetch(get_api("switch/" + toggle.id + (toggle.on ? "/off" : "/on")));
  await updateState(setToggles);

  await toast.hide();
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

export default function Command() {
  const [toggles, setToggles] = useState([]);

  useEffect(() => updateState(setToggles), []); // Or [] if effect doesn't need props or state

  const on = toggles.filter((t) => t.kind == 'switch' && t.on);
  const off = toggles.filter((t) => t.kind == 'switch' && !t.on);
  const controls = toggles.filter((t) => t.kind != 'switch');

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
      <List.Section title="Controls" subtitle={controls.length}>
        {controls.map((toggle) => (
          <SearchListItem key={toggle.name} toggle={toggle} setToggles={setToggles} />
        ))}
      </List.Section>
    </List>
  );
}

function SearchListItem({ toggle, setToggles }) {
  return (
    <List.Item
      id={toggle.id}
      title={toggle.name}
      subtitle={toggle.icon}
      accessories={toggle.alias.map((a) => ({ text: a }))}
      icon={{
        source: toggle.on ? Icon.CircleProgress100 : Icon.Circle,
        tintColor: (toggle.on && toggle.hue) ? hue_to_rgb(toggle.hue) : null,
      }}
      actions={
        <ActionPanel>
          <ActionPanel.Section>
            <Action
              title={`Switch ${toggle.name} ${toggle.on ? "off" : "on"}`}
              onAction={() => run_toggle(toggle, setToggles)}
            />
          </ActionPanel.Section>
          <ActionPanel.Section>
            <Action.CopyToClipboard
              title="Copy Install Command"
              content={`npm install ${toggle.name}`}
              shortcut={{ modifiers: ["cmd"], key: "." }}
            />
          </ActionPanel.Section>
        </ActionPanel>
      }
    />
  );
}
