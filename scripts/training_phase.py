import sqlite3
import sys
import pdb
import io, base64
import Image
DB_PATH = "../db.sqlite3"


def learn(canvas, c, conn):
    for canva in canvas:
	#image_data = re.sub('^data:image/.+;base64,', '', str(canva[1])).decode('base64')
        im = Image.open(io.BytesIO(base64.b64decode(canva[1].split(',')[1])))
        #process to count the pixel of color #069
        count = 0
        for i in range(0, im.size[0]):
            for j in range(0, im.size[1]):
                if im.getpixel((i,j)) != (0, 0, 0, 0):
                    count+=1
        print count
        c.execute('UPDATE authc_canvas SET feature_nbr_pixels_text=? WHERE id=?', (count, canva[0]))
        conn.commit()

def main():
    
    ## Connect to DB 

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT id FROM auth_user')
    users = c.fetchall()
    for user in users:
        c.execute('SELECT * FROM authc_computer WHERE user_id_id=?', user)
        computers = c.fetchall()
        for computer in computers:
            t = (computer[0],)
            c.execute('SELECT * FROM authc_canvas WHERE computer_id_id=?', t)
            canvas =  []
            canvas.append(c.fetchone())
            if canvas[0][5] != -1:
                continue
            else:
                canvas.extend(c.fetchall())
                learn(canvas, c, conn)
    conn.close()
    return 0;


if __name__ == "__main__":
    sys.exit(main())
