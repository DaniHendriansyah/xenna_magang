from odoo import fields, models, api
from odoo.exceptions import UserError

class PinjamBuku(models.Model):
    _name = 'pinjam.buku'
    _description = 'Description'

    siswa = fields.Many2one(comodel_name='data.siswa', string='Nama Siswa', required=True)
    buku = fields.Many2one(comodel_name='data.buku', string='Nama Buku', required=True)
    tanggal_peminjaman = fields.Date(string='Tanggal Peminjaman', required=True, default=fields.Date.context_today)
    tanggal_pengembalian = fields.Date(string='Tanggal Pengembalian', required=True)
    status = fields.Selection([
        ('dipinjam', 'Dipinjam'),
        ('dikembalikan', 'Dikembalikan'),
        ('dikembalikan_terlambat', 'Dikembalikan Terlambat'),
        ], string='Status', readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            buku = self.env['data.buku'].browse(vals.get('buku'))

            if buku and buku.stok <= 0:
                raise UserError(
                    f'Buku "{buku.name}" sedang habis dan tidak dapat dipinjam.'
                )
            
            vals['status'] = 'dipinjam' 
        
        records = super().create(vals_list)

        for record in records:
            
            if record.buku:
                record.buku.stok -= 1

        return records
    
    def action_kembalikan_buku(self):
        for record in self:
            tanggal_hari_ini = fields.Date.context_today(record)

            if tanggal_hari_ini > record.tanggal_pengembalian:
                record.status = 'dikembalikan_terlambat'
            else:
                record.status = 'dikembalikan'

            if record.buku:
                record.buku.stok += 1