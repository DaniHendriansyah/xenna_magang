from odoo import fields, models
from odoo import api, fields, models

class EquipmentLoan(models.Model):
    _name = 'equipment.loan'
    _description = 'Equipment Loan'
    _order = 'id desc'

    borrower_id = fields.Many2one('res.partner', string='Peminjam', required=True)
    borrower_phone = fields.Char(related='borrower_id.phone',string='No. Telepon',readonly=True)
    borrower_email = fields.Char(related='borrower_id.email',string='Email',readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice Denda', readonly=True)
    loan_date = fields.Date(string='Tanggal Pinjam', required=True, default=fields.Date.context_today)
    due_date = fields.Date(string='Jatuh Tempo', required=True)
    duration_days = fields.Integer(string='Durasi (Hari)',compute='_compute_duration_days',store=False)
    return_date = fields.Date(string='Tanggal Dikembalikan', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Sedang Dipinjam'),
        ('returned', 'Dikembalikan'),
        ('late', 'Terlambat'),
        ('lost', 'Hilang'),
    ], string='Status Peminjaman', default='draft', required=True)
    line_notes = fields.Text(string='Kondisi / Catatan')
    loan_line_ids = fields.One2many('equipment.loan.line', 'loan_id', string='Detail Barang')

    def action_confirm(self):
        for record in self:
            if not record.loan_line_ids:
                raise ValueError("Harap pilih minimal satu barang yang akan dipinjam.")
            
            picking_type = self.env['stock.picking.type'].search([
                ('name', '=', 'Peminjaman Alat')
            ], limit=1)
            
            if not picking_type:
                raise ValueError("Operation Type 'Peminjaman Alat' tidak ditemukan. Pastikan sudah dibuat di menu Inventory.")

            src_loc = self.env['stock.location'].search([('complete_name', 'ilike', '%WH/Stock%')], limit=1)
            dest_loc = self.env['stock.location'].search([('complete_name', 'ilike', '%WH/Peminjaman%')], limit=1)

            move_lines = []
            for line in record.loan_line_ids:
                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': src_loc.id,
                    'location_dest_id': dest_loc.id,
                }))

            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': src_loc.id,
                'location_dest_id': dest_loc.id,
                'origin': f"Loan: {record.id}",
                'move_ids_without_package': move_lines,
            })

            picking.action_confirm()
            picking.button_validate()

            record.state = 'ongoing'

    def action_return(self):
        for record in self:
            picking_type = self.env['stock.picking.type'].search([
                ('name', '=', 'Pengembalian Alat')
            ], limit=1)
            
            if not picking_type:
                raise ValueError("Operation Type 'Pengembalian Alat' tidak ditemukan.")

            src_loc = self.env['stock.location'].search([('complete_name', 'ilike', '%WH/Peminjaman%')], limit=1)
            dest_loc = self.env['stock.location'].search([('complete_name', 'ilike', '%WH/Stock%')], limit=1)

            move_lines = []
            for line in record.loan_line_ids:
                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': src_loc.id,
                    'location_dest_id': dest_loc.id,
                }))

            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': src_loc.id,
                'location_dest_id': dest_loc.id,
                'origin': f"Return Loan: {record.id}",
                'move_ids_without_package': move_lines,
            })

            picking.action_confirm()
            picking.button_validate()

            record.state = 'returned'
            record.return_date = fields.Date.context_today(record)

    @api.depends('loan_date', 'due_date', 'return_date', 'state')
    def _compute_duration_days(self):
        for record in self:
            if record.loan_date:
                end_date = record.return_date if record.return_date else record.due_date
                if end_date and end_date >= record.loan_date:
                    delta = end_date - record.loan_date
                    record.duration_days = delta.days + 1 
                else:
                    record.duration_days = 0
            else:
                record.duration_days = 0

    def action_mark_lost(self):
            for record in self:
                if not record.loan_line_ids:
                    raise ValueError("Tidak ada barang dalam daftar peminjaman ini.")

                invoice_lines = []
                for line in record.loan_line_ids:
                    penalty = line.product_id.product_tmpl_id.penalty_fee or line.product_id.list_price or 0.0

                    invoice_lines.append((0, 0, {
                        'name': f"Denda Kehilangan Barang: {line.product_id.name}",
                        'quantity': line.qty,
                        'price_unit': penalty,
                    }))

                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': record.borrower_id.id,
                    'invoice_date': fields.Date.context_today(record),
                    'invoice_line_ids': invoice_lines,
                    'narration': f"Invoice denda peminjaman (ID: {record.id}) - Barang Hilang",
                })

                record.invoice_id = invoice.id
                record.state = 'lost'

    loan_items_summary = fields.Char(
        string='Detail Barang',
        compute='_compute_loan_items_summary',
        store=False
    )

    @api.depends('loan_line_ids', 'loan_line_ids.product_id', 'loan_line_ids.qty')
    def _compute_loan_items_summary(self):
        for record in self:
            items = []
            for line in record.loan_line_ids:
                if line.product_id:
                    items.append(f"{line.product_id.name} ({line.qty}x)")
            record.loan_items_summary = ", ".join(items) if items else "Tidak ada barang"

class EquipmentLoanLine(models.Model):
    _name = 'equipment.loan.line'
    _description = 'Equipment Loan Line'

    loan_id = fields.Many2one('equipment.loan', string='Loan Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Barang', required=True)
    qty = fields.Integer(string='Quantity', default=1, required=True)

    penalty_amount = fields.Float(
        string='Biaya Denda', 
        related='product_id.product_tmpl_id.penalty_fee', 
        readonly=True
    )

    