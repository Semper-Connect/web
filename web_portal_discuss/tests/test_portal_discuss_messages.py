from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestPortalDiscussMessages(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_partner = cls.env["res.partner"].create({"name": "Portal Discuss Member", "email": "portal-discuss-member@example.com"})
        cls.portal_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": cls.portal_partner.name, "login": cls.portal_partner.email,
            "partner_id": cls.portal_partner.id, "share": True,
            "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
        })
        cls.sales_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Portal Sales User", "login": "portal-sales@example.com",
            "share": False, "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        cls.team = cls.env["crm.team"].create({
            "name": "Portal Sales Team", "use_leads": True,
            "crm_team_member_ids": [(0, 0, {"user_id": cls.sales_user.id})],
        })

    def test_portal_sales_channel_is_created_once(self):
        channels = self.env["discuss.channel"]
        first = channels._portal_get_or_create_sales_team_channel(self.portal_partner, self.team)
        second = channels._portal_get_or_create_sales_team_channel(self.portal_partner, self.team)
        self.assertEqual(first, second)
        self.assertEqual(set(first.channel_member_ids.mapped("partner_id").ids), {self.portal_partner.id, self.sales_user.partner_id.id})
        self.assertEqual(len(first.message_ids.filtered(lambda message: message.author_id == self.portal_partner)), 1)

    def test_portal_member_has_access(self):
        channel = self.env["discuss.channel"]._portal_get_or_create_sales_team_channel(self.portal_partner, self.team)
        self.assertTrue(channel._portal_user_has_access(self.portal_user))
        self.assertEqual(channel._portal_check_access(self.portal_user), channel)

    def test_portal_non_member_has_no_access(self):
        other_partner = self.env["res.partner"].create({"name": "Other portal"})
        other_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": other_partner.name, "login": "other-portal@example.com",
            "partner_id": other_partner.id, "share": True,
            "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
        })
        channel = self.env["discuss.channel"]._portal_get_or_create_sales_team_channel(self.portal_partner, self.team)
        with self.assertRaises(AccessError):
            channel._portal_check_access(other_user)
