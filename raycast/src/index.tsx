import { ActionPanel, Action, List, Icon } from "@raycast/api";
import { useFetch } from "@raycast/utils";
import { showToast, Toast } from "@raycast/api";

import { useState, useEffect } from "react";

//https://github.com/raycast/extensions/blob/main/examples/todo-list/src/index.tsx

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
      icon={toggle.on ? Icon.CheckCircle : Icon.Circle}
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
