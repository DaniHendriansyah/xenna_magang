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
            'name': {'label': 'No. Peminjaman', 'order': 'name desc'},
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

    @http.route(['/my/equipment-loans/extend/<int:loan_id>'], type='http', auth="user", methods=['POST'], website=True)
    def request_extension(self, loan_id, **post):
        loan = request.env['equipment.loan'].browse(loan_id)
        
        if loan.borrower_id != request.env.user.partner_id:
            return request.redirect('/my')

        requested_date = post.get('requested_date')
        reason = post.get('reason')

        if requested_date:
            request.env['equipment.loan.extension'].sudo().create({
                'loan_id': loan.id,
                'requested_date': requested_date,
                'reason': reason,
            })
        
        return request.redirect(f'/my/equipment-loans/{loan.id}')

    @http.route(['/my/equipment-loans/new'], type='http', auth="user", website=True)
    def portal_new_loan(self, **kw):
        # Ambil data unit fisik (Serial Number) yang tersedia untuk dipilih
        lots = request.env['stock.lot'].sudo().search([])
        
        values = self._prepare_portal_layout_values()
        values.update({
            'lots': lots,
            'page_name': 'equipment_loan_new',
        })
        return request.render("equipment_loan_tracker.portal_new_loan_form", values)

    @http.route(['/my/equipment-loans/submit'], type='http', auth="user", methods=['POST'], website=True)
    def portal_submit_loan(self, **post):
        partner = request.env.user.partner_id
        loan_date = post.get('loan_date')
        due_date = post.get('due_date')
        lot_id = int(post.get('lot_id'))
        
        lot = request.env['stock.lot'].sudo().browse(lot_id)
        
        new_loan = request.env['equipment.loan'].sudo().create({
            'borrower_id': partner.id,
            'loan_date': loan_date,
            'due_date': due_date,
            'state': 'draft',
        })
        
        request.env['equipment.loan.line'].sudo().create({
            'loan_id': new_loan.id,
            'product_id': lot.product_id.id,
            'lot_id': lot.id,
            'qty': 1,
        })
        
        return request.redirect(f'/my/equipment-loans/{new_loan.id}')