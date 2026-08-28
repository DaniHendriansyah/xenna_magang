from odoo import fields, models, api
from odoo.exceptions import UserError

class DataBuku(models.Model):
    _name = 'data.buku'
    _description = 'Description'

    no_buku = fields.Char(string='Nomor Buku')
    name = fields.Char(string='Nama Buku')
    tahun_terbit = fields.Datetime(string='Tahun Terbit')
    penulis = fields.Char(string='Penulis')
    penerbit = fields.Char(string='Penerbit')
    jumlah_halaman = fields.Integer(string='Jumlah Halaman')
    stok = fields.Integer(string='Stok Tersedia')

    @api.constrains('stok')
    def _check_stok(self):
        for record in self:
            if record.stok < 0:
                raise UserError('Stok buku tidak boleh kurang dari 0.')