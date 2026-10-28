"""Offline regression tests using a minimal Albert interface 5.0 test double."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit


class Action:
    def __init__(self, id, text, callable):
        self.id, self.text, self.callable = id, text, callable


class StandardItem:
    def __init__(self, id=None, text=None, subtext=None, icon_factory=None,
                 actions=None, input_action_text=None):
        self.id = id
        self.text = text
        self.subtext = subtext
        self.icon_factory = icon_factory
        self.actions = actions or []


class PluginInstance:
    def id(self):
        return "aws"

    def readConfig(self, key, type):
        return self.settings.get(key)

    def writeConfig(self, key, value):
        self.settings[key] = value


class GeneratorQueryHandler:
    pass


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.settings = {}
        PluginInstance.settings = self.settings
        albert = ModuleType("albert")
        albert.Action = Action
        albert.StandardItem = StandardItem
        albert.PluginInstance = PluginInstance
        albert.GeneratorQueryHandler = GeneratorQueryHandler
        albert.Icon = SimpleNamespace(image=Mock(return_value="icon"))
        albert.openUrl = Mock()
        modules = patch.dict("sys.modules", {"albert": albert})
        modules.start()
        self.addCleanup(modules.stop)
        spec = importlib.util.spec_from_file_location(
            "aws_plugin", Path(__file__).resolve().parents[1] / "__init__.py")
        self.module = importlib.util.module_from_spec(spec)
        # Albert injects logging helpers into the plugin module before execution.
        self.module.warning = Mock()
        spec.loader.exec_module(self.module)
        self.plugin = self.module.Plugin()
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.plugin.accounts_file = Path(directory.name) / "accounts.json"

    def account_config(self):
        return {
            "portal_url": "https://example.awsapps.com/start",
            "permission_set": "readonly",
            "accounts": [
                {"name": "Example development", "id": "000000000001"},
                {"name": "Example production", "id": "000000000002"},
            ],
        }

    def write_accounts(self, config):
        self.plugin.accounts_file.write_text(json.dumps(config), encoding="utf-8")

    def assert_rejected_accounts(self):
        self.module.warning.reset_mock()
        self.assertEqual(self.plugin.load_services(), [
            {**service, "url": service["url"].format(self.plugin.region)}
            for service in self.module.AWS_URL_LIST
        ])
        self.module.warning.assert_called_once_with(
            "Could not load accounts.json. Check the local account configuration.")

    def items(self, query="", valid=True):
        context = SimpleNamespace(query=query, isValid=valid)
        batches = list(self.plugin.items(context))
        self.assertTrue(all(isinstance(batch, list) for batch in batches))
        return [item for batch in batches for item in batch]

    def test_logging_helper_is_injected_not_imported_from_albert(self):
        import albert

        self.assertFalse(hasattr(albert, "warning"))
        self.plugin.accounts_file.write_text("invalid JSON", encoding="utf-8")
        self.assert_rejected_accounts()

    def test_metadata_trigger_and_icon(self):
        self.assertEqual(self.module.md_iid, "5.0")
        self.assertIsInstance(self.module.md_authors, list)
        self.assertEqual(self.plugin.defaultTrigger(), "aws ")
        self.assertIsInstance(self.plugin, GeneratorQueryHandler)
        item, = self.items()
        self.module.Icon.image.assert_not_called()
        self.assertEqual(item.icon_factory(), "icon")
        icon_path = Path(self.module.__file__).parent / "plugin.svg"
        self.module.Icon.image.assert_called_once_with(icon_path)
        self.assertTrue(icon_path.is_file())

    def test_empty_and_whitespace_queries_show_search_hint(self):
        for query in ("", "   ", "\t\n"):
            with self.subTest(query=query):
                item, = self.items(query)
                self.assertEqual(item.id, "aws/search")
                self.assertEqual(item.subtext, "Search for an AWS service name")
                self.assertEqual(item.actions, [])

    def test_search_is_case_insensitive_and_trims_whitespace(self):
        expected = [service for service in self.module.AWS_URL_LIST
                    if "ec2" in service["name"].lower()]
        items = self.items("  Ec2  ")
        self.assertTrue(items)
        self.assertEqual([item.text for item in items],
                         [service["name"] for service in expected])
        self.assertEqual([item.subtext for item in items],
                         [service["url"].format(self.module.DEFAULT_AWS_REGION)
                          for service in expected])

    def test_region_setting_defaults_and_is_exposed_in_ui(self):
        self.assertEqual(self.plugin.region, "eu-west-1")
        field, = [row for row in self.plugin.configWidget()
                  if row["type"] == "lineedit"]
        self.assertEqual(field["property"], "region")
        self.assertEqual(field["label"], "AWS region")

    def test_region_changes_are_normalised_saved_and_restored(self):
        self.plugin.region = "  EU-CENTRAL-1  "
        self.assertEqual(self.plugin.region, "eu-central-1")
        self.assertEqual(self.settings["region"], "eu-central-1")
        self.assertEqual(self.module.Plugin().region, "eu-central-1")

    def test_blank_region_restores_default(self):
        self.plugin.region = "ap-southeast-2"
        self.plugin.region = "   "
        self.assertEqual(self.plugin.region, "eu-west-1")
        self.assertEqual(self.settings["region"], "eu-west-1")

    def test_invalid_region_does_not_replace_current_setting(self):
        self.plugin.region = "eu-central-1"
        for value in ("invalid", "eu-west-1/elsewhere", "https://example.com", "eu west 1"):
            with self.subTest(value=value):
                self.plugin.region = value
                self.assertEqual(self.plugin.region, "eu-central-1")
                self.assertEqual(self.settings["region"], "eu-central-1")

    def test_invalid_saved_region_falls_back_to_default(self):
        self.settings["region"] = "invalid"
        self.assertEqual(self.module.Plugin().region, "eu-west-1")

    def test_regional_urls_and_actions_change_without_restarting(self):
        original_templates = [dict(service) for service in self.module.AWS_URL_LIST]
        for region in ("eu-central-1", "ap-southeast-2", "eu-west-1"):
            with self.subTest(region=region):
                self.plugin.region = region
                items = self.items("aws")
                for template, item in zip(original_templates, items):
                    self.assertEqual(item.subtext, template["url"].format(region))
                    item.actions[0].callable()
                    self.module.openUrl.assert_called_with(item.subtext)
                urls = {item.text: item.subtext for item in items}
                self.assertEqual(urls["AWS EC2"],
                                 f"https://{region}.console.aws.amazon.com/ec2/home?region={region}#Home:")
                self.assertIn(f"region={region}", urls["AWS S3"])
                self.assertIn(f"region={region}", urls["AWS WAF WebACLs (regional)"])
        self.assertEqual(self.module.AWS_URL_LIST, original_templates)

    def test_added_shortcuts_are_searchable_and_use_configured_region(self):
        names = [
            "AWS VPC Endpoints", "AWS Transit Gateway", "AWS VPC Peering",
            "AWS CloudTrail", "AWS ElastiCache Valkey", "AWS Athena", "AWS Glue",
            "AWS OpenSearch Serverless", "AWS SES", "AWS Batch",
            "AWS EC2 Auto Scaling Groups", "AWS EC2 Launch Templates", "AWS Bedrock",
        ]
        self.plugin.region = "eu-central-1"
        for name in names:
            with self.subTest(name=name):
                matches = [item for item in self.items(name) if item.text == name]
                self.assertEqual(len(matches), 1)
                item, = matches
                self.assertTrue(item.subtext.startswith(
                    "https://eu-central-1.console.aws.amazon.com/"))
                self.assertIn("region=eu-central-1", item.subtext)
                self.assertNotIn("{0}", item.subtext)
                item.actions[0].callable()
                self.module.openUrl.assert_called_with(item.subtext)

    def test_fixed_global_account_and_documentation_links_are_unchanged(self):
        fixed = {service["name"]: service["url"]
                 for service in self.module.AWS_URL_LIST if "{0}" not in service["url"]}
        self.assertTrue(fixed)
        self.plugin.region = "eu-central-1"
        urls = {service["name"]: service["url"] for service in self.plugin.load_services()}
        for name, url in fixed.items():
            self.assertEqual(urls[name], url)

    def test_service_ids_are_unique_and_stable_across_queries(self):
        items = self.items("aws")
        self.assertEqual(len(items), len(self.module.AWS_URL_LIST))
        self.assertEqual(len({item.id for item in items}), len(items))
        ids = {item.text: item.id for item in items}
        for item in self.items("ec2"):
            self.assertEqual(item.id, ids[item.text])

    def test_actions_open_each_services_own_url_only_when_invoked(self):
        items = self.items("aws")
        self.module.openUrl.assert_not_called()
        for item in items:
            self.assertEqual(len(item.actions), 1)
            self.assertEqual(item.actions[0].id, "open")
            item.actions[0].callable()
            self.module.openUrl.assert_called_with(item.subtext)

    def test_fictional_account_shortcuts_preserve_names_ids_and_readonly_urls(self):
        config = self.account_config()
        self.write_accounts(config)
        items = self.items("AWS Account:")
        self.assertEqual(len(items), 2)
        self.assertEqual([item.text for item in items],
                         [f"AWS Account: {account['name']}"
                          for account in config["accounts"]])
        self.module.openUrl.assert_not_called()
        for account, item in zip(config["accounts"], items):
            self.assertEqual(item.subtext,
                             "https://example.awsapps.com/start/#/console?"
                             f"account_id={account['id']}&role_name=readonly")
            self.assertEqual(item.id, f"aws/{item.subtext}")
            self.assertEqual(parse_qs(urlsplit(item.subtext).fragment.split("?", 1)[1]),
                             {"account_id": [account["id"]], "role_name": ["readonly"]})
            self.assertEqual(len(item.actions), 1)
            self.assertEqual(item.actions[0].id, "open")
            item.actions[0].callable()
            self.module.openUrl.assert_called_with(item.subtext)
        self.assertEqual(self.module.openUrl.call_count, 2)
        self.module.warning.assert_not_called()

    def test_portal_shortcut_and_account_links_are_region_independent(self):
        config = self.account_config()
        config["portal_url"] += "/"
        self.write_accounts(config)
        original = self.plugin.load_accounts()
        self.plugin.region = "ap-southeast-2"
        self.assertEqual(self.plugin.load_accounts(), original)
        item, = self.items("AWS Account Portal")
        self.assertEqual(item.subtext, "https://example.awsapps.com/start/#/")
        self.assertEqual(len(item.actions), 1)
        self.module.openUrl.assert_not_called()
        item.actions[0].callable()
        self.module.openUrl.assert_called_once_with(item.subtext)

    def test_account_json_changes_reload_without_restarting(self):
        config = self.account_config()
        self.write_accounts(config)
        self.assertEqual(len(self.items("AWS Account:")), 2)
        config["accounts"] = [{"name": "Example replacement", "id": "000000000002"}]
        config["permission_set"] = "ExampleReader"
        config["portal_url"] = "https://replacement.example.com/start"
        self.write_accounts(config)
        item, = self.items("AWS Account:")
        self.assertEqual(item.text, "AWS Account: Example replacement")
        self.assertEqual(item.subtext,
                         "https://replacement.example.com/start/#/console?"
                         "account_id=000000000002&role_name=ExampleReader")
        item.actions[0].callable()
        self.module.openUrl.assert_called_once_with(item.subtext)
        self.plugin.accounts_file.unlink()
        self.assertEqual(self.plugin.load_accounts(), [])
        self.module.warning.assert_not_called()

    def test_missing_account_file_preserves_builtin_services_without_warning(self):
        self.assertFalse(self.plugin.accounts_file.exists())
        self.assertEqual(self.plugin.load_accounts(), [])
        self.assertEqual(self.plugin.load_services(), [
            {**service, "url": service["url"].format(self.plugin.region)}
            for service in self.module.AWS_URL_LIST
        ])
        self.module.warning.assert_not_called()

    def test_malformed_json_and_encoding_warn_without_disclosing_data(self):
        for content in (b'{"example-secret": "unfinished', b'\xff\xfeexample-secret'):
            with self.subTest(content=content):
                self.plugin.accounts_file.write_bytes(content)
                self.assert_rejected_accounts()

    def test_wrong_account_schema_warns_without_disclosing_data(self):
        invalid = [None, [], "example-secret", 1]
        for field in ("portal_url", "permission_set", "accounts"):
            config = self.account_config()
            del config[field]
            invalid.append(config)
        for field, values in (
            ("portal_url", (None, 1, [])),
            ("permission_set", (None, 1, [], "", " \t")),
            ("accounts", (None, {}, "example-secret")),
        ):
            for value in values:
                config = self.account_config()
                config[field] = value
                invalid.append(config)
        for account in (None, [], "example-secret", {},
                        {"name": "Example incomplete"}, {"id": "000000000001"}):
            config = self.account_config()
            config["accounts"].append(account)
            invalid.append(config)
        for field, values in (
            ("name", (None, 1, "", " \t")),
            ("id", (None, 1, True, 1.0, [], "", "00000000001",
                    "0000000000001", "00000000000x", " 000000000001",
                    "１２３４５６７８９０１２")),
        ):
            for value in values:
                config = self.account_config()
                config["accounts"][1][field] = value
                invalid.append(config)
        for index, config in enumerate(invalid):
            with self.subTest(case=index):
                self.write_accounts(config)
                self.assert_rejected_accounts()

    def test_duplicate_account_ids_reject_entire_configuration(self):
        config = self.account_config()
        config["accounts"][1]["id"] = config["accounts"][0]["id"]
        self.write_accounts(config)
        self.assert_rejected_accounts()

    def test_invalid_portals_warn_without_disclosing_data(self):
        for portal in (
            "", "example.awsapps.com/start", "http://example.awsapps.com/start",
            "https:///start", "https://reader@example.com/start",
            "https://reader:example-secret@example.com/start",
            "https://example.com/start?token=example-secret",
            "https://example.com/start#example-secret", "https://[invalid",
            "https://example.awsapps.com/start#", "https://example.awsapps.com/start?",
            "https://example.awsapps.com:not-a-port/start",
            "https://example.awsapps.com:99999/start",
            "https://example.awsapps.com:0/start", "https://example.awsapps.com:/start",
            "https://bad host/start", "https://example.\tcom/start",
            "\nhttps://example.awsapps.com/start", "https://example.com/start\x00",
            "https://example.com\\elsewhere/start", "https://@example.com/start",
            "https://-example.com/start", "https://example..com/start",
            "https://example_com/start", "https://example.com./start",
        ):
            with self.subTest(portal=portal):
                config = self.account_config()
                config["portal_url"] = portal
                self.write_accounts(config)
                self.assert_rejected_accounts()

    def test_valid_portal_is_reconstructed_from_validated_components(self):
        config = self.account_config()
        config["portal_url"] = "HTTPS://EXAMPLE.AWSAPPS.COM:8443/start/"
        self.write_accounts(config)
        shortcuts = self.plugin.load_accounts()
        self.assertEqual(len(shortcuts), 3)
        self.assertEqual(shortcuts[-1]["url"],
                         "https://example.awsapps.com:8443/start/#/")
        self.assertTrue(shortcuts[0]["url"].startswith(
            "https://example.awsapps.com:8443/start/#/console?"))
        self.module.warning.assert_not_called()

    def test_permission_set_is_encoded_as_one_query_parameter(self):
        config = self.account_config()
        config["permission_set"] = "Example reader + audit/&role_name=admin?#é"
        self.write_accounts(config)
        for account, shortcut in zip(config["accounts"], self.plugin.load_accounts()):
            parsed = urlsplit(shortcut["url"])
            self.assertEqual(parsed.query, "")
            fragment_path, parameters = parsed.fragment.split("?", 1)
            self.assertEqual(fragment_path, "/console")
            self.assertEqual(parse_qs(parameters), {
                "account_id": [account["id"]],
                "role_name": [config["permission_set"]],
            })
            self.assertIn("%26role_name%3Dadmin%3F%23%C3%A9", parameters)
        self.module.warning.assert_not_called()

    def test_unreadable_account_file_warns_without_exception_details(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("example-secret")) as read:
            self.assert_rejected_accounts()
        read.assert_called_once_with(encoding="utf-8")

    def test_example_fixture_is_fictional_and_loads(self):
        example = Path(__file__).resolve().parents[1] / "accounts.example.json"
        config = json.loads(example.read_text(encoding="utf-8"))
        self.assertEqual(config, self.account_config())
        self.write_accounts(config)
        self.assertEqual(self.plugin.load_accounts(), [
            {"name": "AWS Account: Example development",
             "url": "https://example.awsapps.com/start/#/console?"
                    "account_id=000000000001&role_name=readonly"},
            {"name": "AWS Account: Example production",
             "url": "https://example.awsapps.com/start/#/console?"
                    "account_id=000000000002&role_name=readonly"},
            {"name": "AWS Account Portal", "url": "https://example.awsapps.com/start/#/"},
        ])
        self.module.warning.assert_not_called()

    def test_no_matches_show_status_item(self):
        item, = self.items("no-such-service")
        self.assertEqual(item.id, "aws/no-matches")
        self.assertEqual(item.text, "No service matching search string")
        self.assertEqual(item.actions, [])
        self.assertEqual(item.icon_factory(), "icon")

    def test_empty_service_list_shows_no_matches(self):
        with patch.object(self.plugin, "load_services", return_value=[]):
            item, = self.items("ec2")
        self.assertEqual(item.id, "aws/no-matches")

    def test_cancelled_query_does_not_load_services(self):
        with patch.object(self.plugin, "load_services") as load:
            self.assertEqual(self.items("aws", valid=False), [])
        load.assert_not_called()

    def test_cancellation_during_loading_discards_hint_and_results(self):
        for query in ("", "   ", "\t\n", "aws", "no-such-service"):
            with self.subTest(query=query):
                context = SimpleNamespace(query=query, isValid=True)

                def load_services():
                    context.isValid = False
                    return self.module.AWS_URL_LIST

                with patch.object(self.plugin, "load_services", side_effect=load_services):
                    self.assertEqual(list(self.plugin.items(context)), [])

    def test_cancellation_during_search_discards_partial_results(self):
        context = SimpleNamespace(query="aws", isValid=True)

        def services():
            yield self.module.AWS_URL_LIST[0]
            context.isValid = False
            yield self.module.AWS_URL_LIST[1]

        with patch.object(self.plugin, "load_services", return_value=services()):
            self.assertEqual(list(self.plugin.items(context)), [])

    def test_cancellation_before_yield_discards_results(self):
        context = SimpleNamespace(query="aws", isValid=True)

        def services():
            yield self.module.AWS_URL_LIST[0]
            context.isValid = False

        with patch.object(self.plugin, "load_services", return_value=services()):
            self.assertEqual(list(self.plugin.items(context)), [])


if __name__ == "__main__":
    unittest.main()