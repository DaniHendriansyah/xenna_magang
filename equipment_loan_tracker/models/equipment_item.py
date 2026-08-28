from odoo import models, fields

class EquipmentItem(models.Model):
    _name = 'equipment.item'
    _description = 'Data Alat Kantor/Lab'

    name = fields.Char(string='Nama Alat', required=True)
    code = fields.Char(string='Kode Inventaris', required=True, copy=False)
    category = fields.Selection([
        ('laptop', 'Laptop'),
        ('proyektor', 'Proyektor'),
        ('kabel', 'Kabel'),
        ('lainnya', 'Lainnya')
    ], string='Kategori', required=True)
    state = fields.Selection([
        ('available', 'Tersedia'),
        ('on_loan', 'Dipinjam'),
        ('damaged', 'Rusak')
    ], string='Status', default='available', tracking=True)
    notes = fields.Text(string='Catatan Tambahan')

    def action_set_available(self):
        for record in self:
            record.state = 'available'

    def action_set_damaged(self):
        for record in self:
            record.state = 'damaged'