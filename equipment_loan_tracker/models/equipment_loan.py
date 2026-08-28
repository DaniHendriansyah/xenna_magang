from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EquipmentLoanLine(models.Model):
    _name = 'equipment.loan.line'
    _description = 'Detail Peminjaman Alat'

    loan_id = fields.Many2one('equipment.loan', string='Referensi Peminjaman', ondelete='cascade')
    equipment_id = fields.Many2one('equipment.item', string='Alat yang Dipinjam', required=True)
    notes = fields.Char(string='Catatan Kondisi')

class EquipmentLoan(models.Model):
    _name = 'equipment.loan'
    _description = 'Transaksi Peminjaman Alat'

    loan_line_ids = fields.One2many('equipment.loan.line', 'loan_id', string='Daftar Alat')
    equipment_summary = fields.Char(string='Daftar Alat', compute='_compute_equipment_summary')
    
    borrower_id = fields.Many2one('res.users', string='Peminjam', required=True, default=lambda self: self.env.user)
    borrower_phone = fields.Char(string='Nomor Telepon', related='borrower_id.phone', readonly=True)
    loan_date = fields.Date(string='Tanggal Pinjam', default=fields.Date.context_today, required=True)
    due_date = fields.Date(string='Jatuh Tempo', required=True)
    loan_duration = fields.Integer(string='Durasi (Hari)', compute='_compute_loan_duration', store=True)
    return_date = fields.Date(string='Tanggal Dikembalikan', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Sedang Dipinjam'),
        ('returned', 'Dikembalikan'),
        ('late', 'Dipinjam Terlambat'),
        ('returned_late', 'Dikembalikan Terlambat'),
    ], string='Status Peminjaman', default='draft', tracking=True)
    line_notes = fields.Text(string='Kondisi Alat / Catatan')

    def _compute_equipment_summary(self):
        for record in self:
            names = record.loan_line_ids.mapped('equipment_id.name')
            record.equipment_summary = ', '.join(names) if names else '-'

    @api.constrains('loan_line_ids', 'state')
    def _check_equipment_availability(self):
        for record in self:
            if record.state in ['draft', 'ongoing']:
                for line in record.loan_line_ids:
                    if line.equipment_id.state == 'on_loan':
                        raise ValidationError("Alat '%s' saat ini sedang dipinjam dan tidak dapat dibooking." % line.equipment_id.name)

    def action_confirm(self):
        for record in self:
            record.state = 'ongoing'
            for line in record.loan_line_ids:
                line.equipment_id.state = 'on_loan'

    def action_return(self):
        for record in self:
            today = fields.Date.context_today(self)
            record.return_date = today
            for line in record.loan_line_ids:
                line.equipment_id.state = 'available'
                
            if record.due_date and today > record.due_date:
                record.state = 'returned_late'
            else:
                record.state = 'returned'
                
    @api.model
    def _cron_check_late_loans(self):
        today = fields.Date.context_today(self)
        late_loans = self.search([
            ('state', '=', 'ongoing'),
            ('due_date', '<', today)
        ])
        if late_loans:
            late_loans.write({'state': 'late'})

    @api.depends('loan_date', 'due_date')
    def _compute_loan_duration(self):
        for record in self:
            if record.loan_date and record.due_date:
                delta = record.due_date - record.loan_date
                record.loan_duration = delta.days
            else:
                record.loan_duration = 0