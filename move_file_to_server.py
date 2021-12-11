from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
import time
import requests
import pymysql

#webdriver로 크롬 실행.
path = '/opt/homebrew/bin/chromedriver'
driver = webdriver.Chrome(path)

#db접속 준비
conn = pymysql.connect(host='localhost', user='root', password='', charset='utf8', db='music_project')
cur = conn.cursor()

#음원을 받을 수 있는 공유마당 주소로 이동.
driver.get('https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrtSound.do?menuNo=200020&pageUnit=24&sortSe=popular&pageIndex=1')

time.sleep(10)
#for _ in range(53):
#	driver.find_element_by_id('fnNextPageBtn').click()
for j in range(952):
	time.sleep(1)
	n = 25
	start = 1
	for i in range(start, n):
		#j페이지의 i번째 음악 선택
		song = driver.find_element_by_xpath('/html/body/div/div[3]/main/div[2]/div[1]/ul/li[{0}]'.format(i))

		#아용 조건이 조건부 이용이 아닌 경우에만 이동(자유 이용 가능한 음악만)
		try:
			'//*[@id="contents"]/div[1]/ul/li[12]/div[1]/div[2]/span/span/text()'
			cc_by = song.find_element_by_xpath('./div[1]/div[2]/img')
			if cc_by.get_attribute('src').find('license99.png') >= 0 or \
			cc_by.get_attribute('src').find('license01.png') >= 0 or \
			cc_by.get_attribute('src').find('license02.png') >= 0 or \
			cc_by.get_attribute('src').find('license03.png') >= 0 or \
			cc_by.get_attribute('src').find('license04.png') >= 0:
				continue
			else:
				song.find_element_by_xpath('./div[1]/div[1]/span[2]/a').click()
		except:
			cc_by = song.find_element_by_xpath('./div[1]/div[2]/a/img')
			if cc_by.get_attribute('src').find('license99.png') >= 0 or \
			cc_by.get_attribute('src').find('license01.png') >= 0 or \
			cc_by.get_attribute('src').find('license02.png') >= 0 or \
			cc_by.get_attribute('src').find('license03.png') >= 0 or \
			cc_by.get_attribute('src').find('license04.png') >= 0:
				continue
			else:
				song.find_element_by_xpath('./div[1]/div[1]/span[2]/a').click()

		time.sleep(2)

		#현재 음악 페이지 링크에서 wrtSn 정보를 수집
		current_url = driver.current_url
		print(current_url.split('=')[1][:8])
		wrtSn = current_url.split('=')[1][:8]

		#wrtSn 정보를 바탕으로 해당음악 정보를 호출하는 api
		url = 'https://gongu.copyright.or.kr/gongu/wrt/wrtApi/searchDetail.json?wrtSn={0}&apiKey=58af358a-2d87-41c0-b548-af7b90788ca5'.format(wrtSn)

		#해당 음악 정보를 json으로 가져옴
		data = requests.get(url)
		data = data.json()


		#api중 필요한 정보인 wrtSn(저작물 일련번호), authrNm(저작자명), orginSj or altrtvNm(저작물 제목)
		#wrtDc(저작물 설명), #tagNm(저작물 성격 ex.밝은 음악 등)
		#licenseImgUrl(라이센스 형태가 어떤지 사진)을 저장하는 sql 구문 작성.
		sql = 'insert into music_list (wrtSn, author, name, text, tag, url, song_name) values ('
		sql += '"' + data['wrtSn'] + '"' + ', '
		sql += '"' + data['authrNm'] + '"' + ', '
		if data['orginSj'] != '':
			sql += '"' + data['orginSj'] + '"' + ', '
		else:
			sql += '"' + data['altrtvNm'] + '"' + ', '
		sql += '"' + data['wrtDc'] + '"' + ', '
		sql += '"' + data['tagNm'] + '"' + ', '
		sql += '"' + data['licenseImgUrl'] + '"' + ', '

		time.sleep(1)
		try:
			#이용 범위 확인 체크
			check = driver.find_element_by_id('chkDownAt')
			check.click()

			#다운로드 버튼 클릭
			download = driver.find_element_by_id('downChkBtn')
			download.click()

			#설문 조사 창 팝업, 20대 체크
			driver.find_element_by_id('ageSeNo2').click()
			time.sleep(1)

			#음원 사용 체크
			driver.find_element_by_id('visitPurpsNo7').click()
			time.sleep(1)

			#확인 클릭
			driver.find_element_by_id('qestnarBtn').click()
			time.sleep(2)

			#팝업창 닫기
			Alert(driver).accept()
		except:
			pass
		time.sleep(2)

		#다운로드 창으로 페이지 이동
		driver.switch_to.window(driver.window_handles[1])
		time.sleep(2)
		print(driver.title)
		driver.switch_to.frame(driver.find_element_by_id('dext5uploader_frame_dext5upload'))#iframe 이동
		time.sleep(2)

		file_list = driver.find_element_by_xpath('//*[@id="file_list"]')
		lists = file_list.find_elements_by_xpath('./li')
		for lst in lists:
			song_name = lst.find_element_by_xpath("./ul/li[@class='fname']/span").text
			if song_name.find('.mp3') >= 0:#li중 mp3에 해당하는 부분 선택
				sql += '"' + song_name + '"' + ');'#음악 이름을 sql문에 추가
				lst.find_element_by_xpath("./ul/li[@class='input_chk']/input").click()#체크 박스 클릭
				driver.find_element_by_id('button_download').click()#다운로드 버튼 클릭

				#쿼리문 실행
				try:
					cur.execute(sql)
					conn.commit()
					print(sql)
				except pymysql.err.IntegrityError as e:
					print(e)
				except pymysql.err.DataError as e:
					print(e)
				break

		time.sleep(5)

		driver.switch_to.default_content()#iframe 탈출
		time.sleep(1)

		driver.close()
		time.sleep(1)

		driver.switch_to.window(driver.window_handles[0])#원래 페이지로 이동
		time.sleep(1)

		driver.back()#이전 페이지로 이동(음악 메뉴)
		time.sleep(1)
	driver.find_element_by_id('fnNextPageBtn').click()#다음 페이지로 넘김.

conn.close()