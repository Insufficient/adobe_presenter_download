import requests, sys, subprocess, os

# Moodle specific
LOGIN_FAILURE_MSG = 'You are not logged in.'

# Users can get the link by typing into the browser console 
# 'document.getElementById( 'resourceobject' ).src'
def get_link( ):
	url = input( 'Adobe Presenter Base URL: ' )
	return url.replace( '"', '' ).replace( 'index.htm', '' ).replace( '?embed=1', '' )

def get_cookie( ):
	(c_key, c_val) = ( input( 'Cookie Key: '), input( 'Cookie Value: ' ) )
	# defaults to MoodleSession if c_key not provided
	if c_key == '':
		c_key = 'MoodleSession'
	return { c_key: c_val }

def mp3_name( idx ):
	return f'a24x{idx}.mp3'

def download( base_url, output, cookies ):
	idx = 1
	start_url = base_url + '/data/'
	if not os.path.exists( output ):
		os.makedirs( output )
	# download mp3 parts
	while True:
		file = mp3_name( idx )
		url = f'{start_url}/{file}'

		r = requests.get( url, cookies=cookies )

		# we found last part of mp3
		if r.status_code == 404:
			break

		# ensures the the type of the response is a mp3 and not plain text
		if not r.encoding:
			with open( f'{output}/{file}', 'wb' ) as f:
				f.write( r.content )
		else:
			# We failed for one of the parts inbetween
			if idx != 1:
				print( f'Response type expected was {None} but we got {r.encoding}' )
			else:
				if r.text.find( LOGIN_FAILURE_MSG ):
					print( 'Failed to log into Moodle, please re-enter cookies' )
			sys.exit( 1 )

		idx += 1

	# combine files
	if idx != 1:
		arg1 = 'concat:' + '|'.join( [ f'{output}/{mp3_name(x)}' for x in list( range( 1, idx ) ) ] )
		subprocess.run( [ 'ffmpeg', '-i', arg1, '-codec', 'copy', f'{output}.mp3' ] )

def main( ):
	output = input( 'Output Name: ')
	cookies = get_cookie( )
	link = get_link( )
	download( link, output, cookies )

main( )