import json
import urllib2
from datetime import datetime, date, timedelta
import re
import smtplib
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
import csv 
from bs4 import BeautifulSoup
import json

######### FUNCTIONS:

def openUrl(url):
	try:
		page = urllib2.urlopen(url)
		return page.read()
	except urllib2.URLError:
		return False


######### Function that is scraping from D

def soupchik(link):

	html = urllib2.urlopen(link).read()

	soup = BeautifulSoup(html)

	company = {

		# 'company_name': 		soup.find('th', text='Name of Issuer').parent.next_sibling.next_sibling.td.text,
		'street_address':		soup.find('th', text='Street Address 1').parent.next_sibling.next_sibling.td.text,
		'city':					soup.find('th', text='City').parent.next_sibling.next_sibling.td.text,
		'type_of_securities': 	soup.find('table', attrs={'summary': 'Types of Securities Offered'}).find('span', text='X').parent.next_sibling.next_sibling.text,
		'type_of_filing': 		soup.find('table', attrs={'summary': 'Type of Filing'}).find('span', text='X').parent.next_sibling.next_sibling.text,
		'total_offering':		soup.find('table', attrs={'summary': 'Offering and Sales Amounts'}).find('td', text='Total Offering Amount').next_sibling.next_sibling.text,
		'total_sold':			soup.find('table', attrs={'summary': 'Offering and Sales Amounts'}).find('td', text='Total Amount Sold').next_sibling.next_sibling.text,
		'industry':				soup.find('table', attrs={'summary': 'Industry Group'}).find('span', text='X').parent.next_sibling.next_sibling.text,
		# 'date': 				soup.find('table', attrs={'summary': 'Signature Block'}).find('tbody').find('td').next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.text,
		'signer_name':			soup.find('table', attrs={'summary': 'Signature Block'}).find('tbody').findAll('td')[2].text,
		'signer_title':			soup.find('table', attrs={'summary': 'Signature Block'}).find('tbody').find('td').next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.text

	}

	return company


def make_url_and_acc(url_txt):
	p = re.compile("(\d{1,})\/(.*)")
	link = url_txt
	result = re.search(p, link)
	#Central index key
	CIK = result.group(1)
	#Accession number 
	ACC_NUM = result.group(2)
	ACC_NUM = ACC_NUM.replace(".txt", "")
	ACC_NUM_NO_DASH = ACC_NUM.replace("-", "")
	ACC_NUM_WITH_INDEX = ACC_NUM + "-index.html"
	FULL_URL = "https://www.sec.gov/Archives/edgar/data/" + CIK + "/" + ACC_NUM_NO_DASH + "/" + ACC_NUM_WITH_INDEX
	to_return = {
		"full_url": FULL_URL,
		"acc_num": ACC_NUM
	}
	return to_return




######### APP CORE CODE

creds = ''
with open("cred.json", "r") as f:
	creds = json.load(f)

d = date.today() - timedelta(days=1)

date = d.strftime("%Y%m%d")

# date = "20150723"

url = "ftp://ftp.sec.gov/edgar/daily-index/form." + date + ".idx"

forms = ["D", "8-K", "10-K", "10-Q"]

# Loading zips from a csv file to a list

zips = []

with open('origin_zips.csv') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		zips.append(row['zip'])

# end load zips


page = openUrl(url)

matches = []

if page:
	by_lines = page.split("\n")
	by_lines = by_lines[11:]

	# This piece of code will count how many rows there are
	total_to_visit = 0
	for line in by_lines:
		p = re.compile( '\s{2,}')
		line = p.sub( ';', line)
		line = line[:-1]
		line_as_list = line.split(";")
		if line_as_list[0] in forms:
			total_to_visit = total_to_visit + 1
	print 'Total URLs that I will visit: ' + str(total_to_visit)

	# Go through every row again, just like before, but this time do some real actions, not just count rows
	for line in by_lines:

		p = re.compile( '\s{2,}')
		line = p.sub( ';', line)
		line = line[:-1]
		line_as_list = line.split(";")

		#Line_as_list structure: 
			# lines_as_list[0] - form type
			# lines_as_list[1] - company name
			# lines_as_list[2] - cik
			# lines_as_list[3] - date 
			# lines_as_list[4] - link
			# lines_as_list[5] - state
		form = line_as_list[0]
		if form in forms:
			total_to_visit = total_to_visit - 1
			print 'Left URLs to visit: ' + str(total_to_visit)
			detail_url = "ftp://ftp.sec.gov/" + line_as_list[4]
			detail_page = urllib2.urlopen(detail_url).read()
			detail_page_by_lines = detail_page.split("\n")

			if form == "10-K" or form == '10-Q':
				zip = detail_page_by_lines[30]
			elif form == '8-K':
				zip = detail_page_by_lines[32]
			else: # if form D
				zip = detail_page_by_lines[33]

			new_URL = line_as_list[4].replace("-", "")

			p = re.compile('\d{5}')
			result = re.search(p, zip)
			try:
				zip = result.group(0)
			except:
				zip = 'ERROR'
			if zip in zips:

				url_and_acc = make_url_and_acc(line_as_list[4])

				filing_date = line_as_list[3]
				filing_date = filing_date[:4] + '-' + filing_date[4:6] + '-' + filing_date[6:]

				company = {
					'form': form,
					'name': line_as_list[1],
					'date': filing_date,
					'cik': line_as_list[2],
					'url': url_and_acc["full_url"],
					'acc_num': url_and_acc["acc_num"]
				}

				if form == 'D':
					form_d_dict = soupchik(url_and_acc["full_url"])
					company.update(form_d_dict) #method update allows glueing two dicts together

				print company
					
				matches.append(company)

with open("matches.json", "w") as f:
	json.dump(matches, f)


# print matches

# send_email(matches)



# ftp://ftp.sec.gov/edgar/data/845698/0000913849-15-000181.txt
# https://www.sec.gov/Archives/edgar/data/845698/000091384915000183/0000913849-15-000183-index.htm