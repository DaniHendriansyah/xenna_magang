from odoo import fields, models

class DashboardPerpustakaan(models.Model):
    _name = 'dashboard.perpustakaan'
    _description = 'Dashboard Perpustakaan'

    name = fields.Char(
        string='Nama',
        default='Dashboard Perpustakaan'
    )

    total_buku = fields.Integer(
        string='Total Buku',
        compute='_compute_statistik'
    )

    total_siswa = fields.Integer(
        string='Total Siswa',
        compute='_compute_statistik'
    )

    sedang_dipinjam = fields.Integer(
        string='Sedang Dipinjam',
        compute='_compute_statistik'
    )

    terlambat = fields.Integer(
        string='Dikembalikan Terlambat',
        compute='_compute_statistik'
    )

    def _compute_statistik(self):
        Buku = self.env['data.buku']
        Siswa = self.env['data.siswa']
        Pinjam = self.env['pinjam.buku']

        for record in self:
            record.total_buku = Buku.search_count([])
            record.total_siswa = Siswa.search_count([])
            record.sedang_dipinjam = Pinjam.search_count([
                ('status', '=', 'dipinjam')
            ])
            record.terlambat = Pinjam.search_count([
                ('status', '=', 'dikembalikan_terlambat')
            ])

class BukuTerpopuler(models.Model):
    _name = 'buku.terpopuler'
    _description = 'Buku Paling Sering Dipinjam'
    _order = 'jumlah_pinjam desc'

    buku = fields.Many2one(
        'data.buku',
        string='Buku',
        readonly=True
    )

    jumlah_pinjam = fields.Integer(
        string='Jumlah Dipinjam',
        readonly=True
    )