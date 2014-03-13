def render_metadata(extracted_metadata):
    with sqlite3.connect('metadata.sqlite') as connection:
        cursor = connection.cursor()
        cursor.execute('''create table metadata (
        id integer primary key,
        pv2_1 float,
        pv2_3 float,
        pv2_5 float,
        cd1_1 float,
        cd1_2 float,
        cd2_1 float,
        cd2_2 float,
        cmd_ra float,
        cmd_dec float,
        tel_ra float,
        tel_dec float,
        actionid integer,
        exposure float,
        cts_med float,
        airmass float,
        skylevel float,
        ra_offset float,
        dec_offset float,
        filename string
        )''')

        cursor.executemany('''insert into metadata (
        pv2_1,
        pv2_3,
        pv2_5,
        cd1_1,
        cd1_2,
        cd2_1,
        cd2_2,
        cmd_ra,
        cmd_dec,
        tel_ra,
        tel_dec,
        actionid,
        exposure,
        cts_med,
        airmass,
        skylevel,
        ra_offset,
        dec_offset,
        filename
        ) values (
        :pv2_1,
        :pv2_3,
        :pv2_5,
        :cd1_1,
        :cd1_2,
        :cd2_1,
        :cd2_2,
        :cmd_ra,
        :cmd_dec,
        :tel_ra,
        :tel_dec,
        :actionid,
        :exposure,
        :cts_med,
        :airmass,
        :skylevel,
        :ra_offset,
        :dec_offset,
        :filename)''', extracted_metadata)


