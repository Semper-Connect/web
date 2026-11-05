from odoo import api, models
from odoo.osv import expression
from odoo.tools import SQL
from odoo.addons.mail.tools.discuss import Store


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.readonly
    @api.model
    def search_for_channel_invite(self, search_term, channel_id=None, limit=30):
        """Allow internal users to invite active portal users to Discuss channels."""
        domain = expression.AND([
            expression.OR([
                [("name", "ilike", search_term)],
                [("email", "ilike", search_term)],
            ]),
            [("active", "=", True)],
            [("user_ids", "!=", False)],
            [("user_ids.active", "=", True)],
        ])
        channel = self.env["discuss.channel"]
        if channel_id:
            channel = self.env["discuss.channel"].search(
                [("id", "=", int(channel_id))], limit=1
            )
            domain = expression.AND([
                domain,
                [("channel_ids", "not in", channel.id)],
            ])
            if channel.group_public_id:
                domain = expression.AND([
                    domain,
                    expression.OR([
                        [("user_ids.groups_id", "in", channel.group_public_id.id)],
                        [
                            ("user_ids.share", "=", True),
                            ("user_ids.groups_id", "in", self.env.ref("base.group_portal").id),
                        ],
                    ]),
                ])
        query = self._search(domain, limit=limit)
        query.order = SQL(
            'LOWER(%s), "res_partner"."id"',
            self._field_to_sql(self._table, "name"),
        )
        partners = self.browse(query)
        store = Store()
        partners._search_for_channel_invite_to_store(store, channel)
        return {
            "count": self.search_count(domain),
            "data": store.get_result(),
        }
