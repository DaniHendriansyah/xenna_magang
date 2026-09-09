from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError

class EquipmentLoanPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'equipment_loan_count' in counters:
            partner = request.env.user.partner_id
            count = request.env['equipment.loan'].search_count([('borrower_id', '=', partner.id)])
            values['equipment_loan_count'] = count
        return values

    @http.route(['/my/equipment-loans', '/my/equipment-loans/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipment_loans(self, page=1, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Loan = request.env['equipment.loan']

        domain = [('borrower_id', '=', partner.id)]

        searchbar_sortings = {
            'date': {'label': 'Tanggal Pinjam', 'order': 'loan_date desc'},
            'due': {'label': 'Jatuh Tempo', 'order': 'due_date asc'},
            'state': {'label': 'Status', 'order': 'state'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': 'Semua', 'domain': []},
            'ongoing': {'label': 'Sedang Dipinjam', 'domain': [('state', '=', 'ongoing')]},
            'late': {'label': 'Terlambat', 'domain': [('state', '=', 'late')]},
            'returned': {'label': 'Dikembalikan', 'domain': [('state', '=', 'returned')]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        loan_count = Loan.search_count(domain)
        pager = portal_pager(
            url="/my/equipment-loans",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=loan_count,
            page=page,
            step=10
        )

        loans = Loan.search(domain, order=order, limit=10, offset=pager['offset'])
        
        values.update({
            'loans': loans,
            'page_name': 'equipment_loan',
            'pager': pager,
            'default_url': '/my/equipment-loans',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
        })
        return request.render("equipment_loan_tracker.portal_my_equipment_loans_template", values)

    @http.route(['/my/equipment-loans/<int:loan_id>'], type='http', auth="public", website=True)
    def portal_my_equipment_loan_detail(self, loan_id, access_token=None, **kw):
        try:
            loan_sudo = self._document_check_access('equipment.loan', loan_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my/equipment-loans')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'loan': loan_sudo,
            'page_name': 'equipment_loan',
        })
        
        return request.render("equipment_loan_tracker.portal_equipment_loan_detail_template", values)