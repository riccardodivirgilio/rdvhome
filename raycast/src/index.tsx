import { ActionPanel, Action, List, Icon } from "@raycast/api";
import { useFetch, Response } from "@raycast/utils";
import { useState } from "react";
import { URLSearchParams } from "node:url";
import { showHUD, Clipboard } from "@raycast/api";

export async function run_toggle(toggle: RemoteSwitch) {

  fetch(get_api('switch/' +toggle.id+ ( toggle.on ? '/off' : '/on')));

  await showHUD(`Switched ${toggle.on ? 'off' : 'on'} ${toggle.name}`);
}

function get_api(path: string) {
  return "http://rdvhome.local:8500/" + path;
}

export default function Command() {
  const { data, isLoading } = useFetch(get_api("switch"), {
    parseResponse: parseFetchResponse,
  });

  return (
    <List isLoading={isLoading} searchBarPlaceholder="Search lights...">
      <List.Section title="Switches" subtitle={data?.length + ""}>
        {data?.map((toggle) => (
          <SearchListItem key={toggle.name} toggle={toggle} />
        ))}
      </List.Section>
    </List>
  );
}

function SearchListItem({ toggle }: { toggle: RemoteSwitch }) {
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
            <Action title={`Switch ${toggle.name} ${toggle.on ? 'off' : 'on'}`} onAction={() => run_toggle(toggle)} />
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

/** Parse the response from the fetch query into something we can display */
async function parseFetchResponse(response: Response) {
  const json = (await response.json()) as
    | {
        switches: { [key: string]: RemoteSwitch };
      }
    | { status: integer; reason: string };

  if (!response.ok || "reason" in json) {
    throw new Error("message" in json ? json.reason : response.statusText);
  }

  return Object.values(json.switches).filter(toggle => toggle.allow_visibility);
}

interface RemoteSwitch {
  id: string;
  name: string;
  kind: string;
  icon: string;
  hue?: number;
  brightness?: number;
  saturation?: number;
  on?: bool;
  alias: [string];
  allow_visibility?: bool
}
