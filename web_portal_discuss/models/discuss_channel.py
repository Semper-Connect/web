from odoo import _, api, models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    @api.model
    def _portal_get_or_create_sales_team_channel(self, portal_partner, sales_team):
        """Return one idempotent portal conversation for a customer and team."""
        sales_partners = sales_team.crm_team_member_ids.filtered(
            lambda member: member.active
            and member.user_id.active
            and not member.user_id.share
        ).mapped("user_id.partner_id")
        if not sales_partners:
            return self.browse()

        partner_ids = (sales_partners | portal_partner).ids
        channels = self.sudo().search(
            [
                ("channel_type", "=", "group"),
                ("channel_member_ids.partner_id", "=", portal_partner.id),
            ],
            order="id",
        )
        for channel in channels:
            if set(channel.channel_member_ids.mapped("partner_id").ids) == set(partner_ids):
                return channel

        channel = self.sudo().create(
            {
                "name": _(
                    "%(team)s - %(customer)s",
                    team=sales_team.name,
                    customer=portal_partner.name,
                ),
                "channel_type": "group",
                "channel_partner_ids": [(6, 0, partner_ids)],
            }
        )
        channel.message_post(
            body=_(
                "New discussion opened by %(customer)s for the sales team %(team)s.",
                customer=portal_partner.name,
                team=sales_team.name,
            ),
            message_type="comment",
            author_id=portal_partner.id,
        )
        return channel
