#This bot was originally written by /u/GoldenSights for /u/FourMakesTwoUNLESS on behalf of /r/pkmntcgtrades.
# Modified version by /u/FlapSnapple
import praw
import time
import datetime
import sqlite3

'''USER CONFIGURATION'''

USERNAME = "username"
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD = "password"
#This is the bot's Password. 
USERAGENT = "/r/amiiboSwap Delay Checker to enforce one trade post every 7 days rule"
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter Bot"
SUBREDDIT = "amiiboSwap"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 30
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
DELAY = 604800 #7 Days
#This is the time limit between a user's posts, IN SECONDS. 1h = 3600 || 12h = 43200 || 24h = 86400 || 144h = 518400

'''All done!'''






WAITS = str(WAIT)
sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(name TEXT, lastpost TEXT)')
print('Loaded Users')
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
print('Loaded Oldposts')
sql.commit()

r = praw.Reddit(USERAGENT)

Trying = True
while Trying:
	try:
		r.login(USERNAME, PASSWORD)
		print('Successfully logged in')
		Trying = False
	except praw.errors.InvalidUserPass:
		print('Wrong Username or Password')
		quit()
	except Exception as e:
		print("%s" % e)
		time.sleep(5)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def scan():
	print('Scanning ' + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		try:
			pauthor = post.author.name
		except Exception:
			pauthor = '[deleted]'
		pid = post.id
		plink = post.short_link
		ptime = post.created_utc
		cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
		if not cur.fetchone():
			cur.execute('SELECT * FROM users WHERE name=?', [pauthor])
			if not cur.fetchone():
				print('Found new user: ' + pauthor)
				cur.execute('INSERT INTO users VALUES(?, ?)', (pauthor, pid))
				#r.send_message(pauthor, 'Welcome','Dear ' + pauthor + ',\n\n This appears to be your first time posting on /r/amiiboSwap. here', captcha=None)
				sql.commit()
				print('\t' + pauthor + ' has been added to the database.')
				time.sleep(5)
			else:
				cur.execute('SELECT * FROM users WHERE name=?', [pauthor])
				fetch = cur.fetchone()
				print('Found post by known user: ' + pauthor)
				previousid = fetch[1]
				previous = r.get_info(thing_id='t3_'+previousid)
				previoustime = previous.created_utc
				if ptime > previoustime:
					curtime = getTime(True)
					difference = curtime - previoustime
					if difference >= DELAY:
						print('\tPost complies with timelimit guidelines. Permitting')
						cur.execute('DELETE FROM users WHERE name=?', [pauthor])
						cur.execute('INSERT INTO users VALUES(?, ?)', (pauthor, pid))
						sql.commit()
						print('\t' + pauthor + "'s database info has been reset.")
					else:
						differences = '%.0f' % (DELAY - difference)
						timestring = str(datetime.timedelta(seconds=float(differences)))
						timestring = timestring.replace(':', ' hours, and ', 1)
						timestring = timestring.replace(':', ' minutes.x', 1)
						timestring = timestring.split('x')
						timestring = timestring[0]
						print('\tPost does not comply with timelimit guidelines. Author must wait ' + timestring)
						print('\t' + pauthor + "'s database info remains unchanged")
						response = post.add_comment('According to the rules of /r/amiiboSwap, you are only allowed one post every 7 days, so your post has been deleted. You may post again in ' + str(timestring))
						response.distinguish()
						post.remove(spam=False)
						time.sleep(5)
			cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
		sql.commit()




while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured:', e)
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)