import { ActionPanel, Action, List, Icon } from "@raycast/api"
import { useFetch } from "@raycast/utils"
import { showHUD } from "@raycast/api"

//https://github.com/raycast/extensions/blob/main/examples/todo-list/src/index.tsx

export async function run_toggle(toggle) {
  fetch(get_api("switch/" + toggle.id + (toggle.on ? "/off" : "/on")))

  await showHUD(`Switched ${toggle.on ? "off" : "on"} ${toggle.name}`)
}

function get_api(path) {
  return "http://rdvhome.local:8500/" + path
}



export default function Command() {

  const { data, isLoading } = useFetch(get_api("switch"), {
    parseResponse: r => parseFetchResponse(r)
  })

  const on = data.filter(t => t.on)
  const off = data.filter(t => ! t.on)

  return (
    <List isLoading={isLoading} searchBarPlaceholder="Search lights...">
      <List.Section title="On" subtitle={on.length + ""}>
        {on.map(toggle => (
          <SearchListItem key={toggle.name} toggle={toggle} />
        ))}
      </List.Section>
      <List.Section title="Off" subtitle={off.length + ""}>
        {off.map(toggle => (
          <SearchListItem key={toggle.name} toggle={toggle} />
        ))}
      </List.Section>
    </List>
  )
}

function SearchListItem({ toggle }) {
  return (
    <List.Item
      id={toggle.id}
      title={toggle.name}
      subtitle={toggle.icon}
      accessories={toggle.alias.map(a => ({ text: a }))}
      icon={toggle.on ? Icon.CheckCircle : Icon.Circle}
      actions={
        <ActionPanel>
          <ActionPanel.Section>
            <Action
              title={`Switch ${toggle.name} ${toggle.on ? "off" : "on"}`}
              onAction={() => run_toggle(toggle)}
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
  )
}

/** Parse the response from the fetch query into something we can display */
async function parseFetchResponse(response) {
  const json = await response.json()

  if (!response.ok || "reason" in json) {
    throw new Error("message" in json ? json.reason : response.statusText)
  }

  return Object.values(json.switches).filter(toggle => toggle.allow_visibility)
}
