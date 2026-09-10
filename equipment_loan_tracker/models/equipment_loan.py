from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta
from markupsafe import Markup

class EquipmentLoan(models.Model):
    _name = 'equipment.loan'
    _description = 'Equipment Loan'
    _order = 'id desc'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string='No. Peminjaman', compute='_compute_name', store=True)
    borrower_id = fields.Many2one('res.partner', string='Peminjam', required=True)
    borrower_phone = fields.Char(related='borrower_id.phone', string='No. Telepon', readonly=True)
    borrower_email = fields.Char(related='borrower_id.email', string='Email', readonly=True)

    invoice_id = fields.Many2one('account.move', string='Invoice Denda', readonly=True)

    loan_date = fields.Date(string='Tanggal Pinjam', required=True, default=fields.Date.context_today)
    due_date = fields.Date(string='Jatuh Tempo', required=True)
    duration_days = fields.Integer(string='Durasi (Hari)', compute='_compute_duration_days', store=False)
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

    loan_items_summary = fields.Char(
        string='Detail Barang',
        compute='_compute_loan_items_summary',
        store=False
    )

    @api.depends('create_date', 'write_date')
    def _compute_name(self):
        for record in self:
            if record.id:
                record.name = f"LOAN/{record.id:04d}"
            else:
                record.name = "Draft"

    def _compute_access_url(self):
        super()._compute_access_url()
        for loan in self:
            loan.access_url = f'/my/equipment-loans/{loan.id}'

    def _check_date_overlap(self):
        for loan in self:
            if loan.state not in ['draft', 'ongoing']:
                continue
            
            for line in loan.loan_line_ids:
                if not line.lot_id:
                    continue
                
                overlap_domain = [
                    ('id', '!=', loan.id),
                    ('state', 'in', ['draft', 'ongoing']),
                    ('loan_line_ids.lot_id', '=', line.lot_id.id),
                    ('loan_date', '<', loan.due_date),
                    ('due_date', '>', loan.loan_date)
                ]
                
                overlapping_loans = self.search_count(overlap_domain)
                if overlapping_loans > 0:
                    raise ValidationError(
                        f"Unit {line.lot_id.name} ({line.product_id.name}) sudah dibooking "
                        f"pada rentang tanggal {loan.loan_date} s/d {loan.due_date}."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_date_overlap()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ['loan_date', 'due_date', 'state', 'loan_line_ids']):
            self._check_date_overlap()
        return res

    def action_confirm(self):
        self._check_date_overlap()
        for record in self:
            if not record.loan_line_ids:
                raise ValueError("Harap pilih minimal satu barang yang akan dipinjam.")
            
            picking_type = self.env['stock.picking.type'].search([
                ('name', '=', 'Peminjaman Alat')
            ], limit=1)
            
            if not picking_type:
                raise ValueError("Operation Type 'Peminjaman Alat' tidak ditemukan.")

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
                'partner_id': record.borrower_id.id,
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

    @api.depends('loan_line_ids', 'loan_line_ids.product_id', 'loan_line_ids.qty', 'loan_line_ids.lot_id')
    def _compute_loan_items_summary(self):
        for record in self:
            items = []
            for line in record.loan_line_ids:
                if line.product_id:
                    serial = f" [SN: {line.lot_id.name}]" if line.lot_id else ""
                    items.append(f"{line.product_id.name}{serial} ({line.qty}x)")
            record.loan_items_summary = ", ".join(items) if items else "Tidak ada barang"

    @api.model
    def _cron_send_loan_reminders(self):
        """Cron job harian untuk Reminder H-1 dan Overdue Alert"""
        today = fields.Date.context_today(self)
        tomorrow = today + timedelta(days=1)
        
        reminder_loans = self.search([
            ('state', '=', 'ongoing'),
            ('due_date', '=', tomorrow)
        ])
        template_reminder = self.env.ref('equipment_loan_tracker.email_template_equipment_loan_reminder', raise_if_not_found=False)
        for loan in reminder_loans:
            if template_reminder and loan.borrower_id.email:
                template_reminder.send_mail(loan.id)

        overdue_loans = self.search([
            ('state', '=', 'ongoing'),
            ('due_date', '<', today)
        ])
        template_overdue = self.env.ref('equipment_loan_tracker.email_template_equipment_loan_overdue', raise_if_not_found=False)
        for loan in overdue_loans:
            loan.state = 'late'
            if template_overdue and loan.borrower_id.email:
                template_overdue.send_mail(loan.id)

class EquipmentLoanExtension(models.Model):
    _name = 'equipment.loan.extension'
    _description = 'Equipment Loan Extension Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    loan_id = fields.Many2one('equipment.loan', string='Loan Reference', required=True, ondelete='cascade')
    borrower_id = fields.Many2one(related='loan_id.borrower_id', store=True, string='Borrower')
    requested_date = fields.Date(string='Requested Extension Date', required=True)
    reason = fields.Text(string='Reason')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', tracking=True)

    def action_approve(self):
        for record in self:
            record.loan_id.write({'due_date': record.requested_date})
            record.state = 'approved'
            
            msg_body = Markup(f"""
                <div style="margin: 0; padding: 15px; font-family: Arial, sans-serif; color: #333333; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f9f9f9;">
                    <p>Yth. <strong>{record.borrower_id.name}</strong>,</p>
                    <p>Permohonan perpanjangan waktu peminjaman alat Anda telah <span style="color: #198754; font-weight: bold;">DISETUJUI</span>.</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; background-color: #ffffff; padding: 10px; border: 1px solid #dee2e6;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; width: 35%;"><strong>No. Peminjaman</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">: {record.loan_id.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Detail Barang</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">: {record.loan_id.loan_items_summary}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;"><strong>Jatuh Tempo Baru</strong></td>
                            <td style="padding: 8px; color: #dc3545; font-weight: bold;">: {record.requested_date.strftime('%d %B %Y')}</td>
                        </tr>
                    </table>
                    
                    <p>Harap pastikan alat dikembalikan tepat waktu sebelum atau pada tanggal jatuh tempo yang baru untuk menghindari denda.</p>
                    <br/>
                    <p>Terima kasih,<br/><strong>Administrator Peminjaman</strong></p>
                </div>
            """)
            
            record.loan_id.message_post(
                body=msg_body,
                subject=f"Disetujui: Perpanjangan Peminjaman {record.loan_id.name}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[record.borrower_id.id]
            )

    def action_reject(self):
        for record in self:
            record.state = 'rejected'
            
            msg_body = Markup(f"""
                <div style="margin: 0; padding: 15px; font-family: Arial, sans-serif; color: #333333; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #fff3f3;">
                    <p>Yth. <strong>{record.borrower_id.name}</strong>,</p>
                    <p>Mohon maaf, permohonan perpanjangan waktu peminjaman alat Anda <span style="color: #dc3545; font-weight: bold;">DITOLAK</span>.</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; background-color: #ffffff; padding: 10px; border: 1px solid #dee2e6;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; width: 35%;"><strong>No. Peminjaman</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">: {record.loan_id.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Detail Barang</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">: {record.loan_id.loan_items_summary}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;"><strong>Alasan Penolakan</strong></td>
                            <td style="padding: 8px; color: #dc3545;">: {record.reason or 'Tidak ada keterangan spesifik dari admin.'}</td>
                        </tr>
                    </table>
                    
                    <p>Harap segera mengembalikan barang tersebut sesuai dengan tanggal jatuh tempo awal yang telah disepakati.</p>
                    <br/>
                    <p>Terima kasih,<br/><strong>Administrator Peminjaman</strong></p>
                </div>
            """)
            
            record.loan_id.message_post(
                body=msg_body,
                subject=f"Ditolak: Perpanjangan Peminjaman {record.loan_id.name}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[record.borrower_id.id]
            )

    def _get_mail_redirect_url(self):
        """ Override router bawaan Odoo agar tombol email selalu mengarah ke portal mandiri """
        self.ensure_one()
        return f'/my/equipment-loans/{self.id}'

class EquipmentLoanLine(models.Model):
    _name = 'equipment.loan.line'
    _description = 'Equipment Loan Line'

    loan_id = fields.Many2one('equipment.loan', string='Loan Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Barang', required=True)
    
    lot_id = fields.Many2one(
        'stock.lot', 
        string='Serial Number', 
        domain="[('product_id', '=', product_id)]",
        required=True,
        help="Pilih unit fisik spesifik yang akan dipinjam."
    )
    
    qty = fields.Integer(string='Quantity', default=1, required=True)

    penalty_amount = fields.Float(
        string='Biaya Denda', 
        related='product_id.product_tmpl_id.penalty_fee', 
        readonly=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.lot_id = False
        if self.product_id:
            self.qty = 1