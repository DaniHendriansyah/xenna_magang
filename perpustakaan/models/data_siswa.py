from odoo import fields, models, api

class DataSiswa(models.Model):
    _name = 'data.siswa'
    _description = 'Data Siswa'

    name = fields.Char(string='Nama Siswa', required=True)
    umur = fields.Integer(string='Umur', required=True)
    nis = fields.Integer(string='NIS')
    kelas = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ], string='Kelas')
    tanggal_lahir = fields.Date(string='Tanggal Lahir', required=True)
    tempat_lahir = fields.Char(string='Tempat Lahir', required=True)

    def action_lihat_riwayat(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Riwayat Peminjaman',
            'res_model': 'pinjam.buku',
            'view_mode': 'list,form',
            'domain': [
                ('siswa', '=', self.id)
            ],
        }