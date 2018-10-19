from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import time
from PIL import Image, ImageFilter
import requests
import cv2
import numpy as np
from matplotlib import pyplot as plt
from match_image import ImageMatcher
import random


class Hack(object):
    def __init__(self, url, **kw):
        driver = webdriver.Chrome()
        driver.implicitly_wait(4)
        driver.get(url)
        self.driver = driver
        self.width_margin = 0
        self.element_getter = None
        print(kw)
        if 'width_margin' in kw:
            self.width_margin = kw.get('width_margin')

    def get_driver(self):
        return self.driver

    def run(self, element_getter):
        self.element_getter = element_getter
        element_getter.get_popup_btn().click()
        time.sleep(3)
        self.match()

    def match(self):
        img = cv2.imread(self.element_getter.get_whole_file_name(), 0)
        img2 = img.copy()
        template = cv2.imread(self.element_getter.get_fragment_file_name(), 0)
        w, h = template.shape[::-1]
        # All the 6 methods for comparison in a list TM_CCOEFF_NORMED TM_CCORR_NORMED
        # methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
        #            'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
        methods = ['cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF_NORMED']
        left_dis = []
        for meth in methods:
            img = img2.copy()
            method = eval(meth)

            # Apply template Matching
            res = cv2.matchTemplate(img, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                top_left = min_loc
            else:
                top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            if top_left[0] > 0:
                left_dis.append(top_left[0])
            # print(top_left, bottom_right)
            # print(top_left[0])

            # cv2.rectangle(img, top_left, bottom_right, 255, 2)
            #
            # plt.subplot(121), plt.imshow(res, cmap='gray')
            # plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
            # plt.subplot(122), plt.imshow(img, cmap='gray')
            # plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
            # plt.suptitle(meth)
            # plt.show()
        actions = ActionChains(self.driver)
        actions.move_to_element(self.element_getter.get_slider_btn())

        actions.click_and_hold()

        move_dis = 100
        if len(left_dis) > 0:
            move_dis = left_dis[0]
        print('moveLeft', move_dis)
        moved = 0
        while moved < move_dis + 25:
            to_move = random.random()*30
            actions.move_by_offset(to_move, random.random()*20 - 10)
            if random.random() > 0.3:
                actions.pause(random.random())
            moved += to_move
        print(moved)
        # move_margin = move_dis + 25 - moved
        # print(move_margin)
        # actions.move_by_offset(move_margin, 10)

        # actions.move_by_offset(move_dis / 2, 10)
        # actions.pause(1)
        # actions.move_by_offset(move_dis / 2, 5)
        # actions.pause(1)
        # actions.move_by_offset(25, 20)
        # actions.pause(1)

        actions.release()
        actions.perform()
        try:
            success = self.element_getter.success_mark()
            if success:
                print('success')
                time.sleep(3)
            else:
                print('fail')
                self.retry()
        except:
            print('fail')
            self.retry()

    def retry(self):
        time.sleep(1)
        refresh_btn = self.element_getter.get_refresh_btn()
        refresh_btn.click()
        time.sleep(1)
        self.match()


class ElementGetter(object):
    def __init__(self, driver):
        self.driver = driver

    def by_class_name(self, class_name):
        return self.driver.find_element_by_class_name(class_name)

    def get_popup_btn(self, class_name):
        return self.by_class_name(class_name)

    def get_slider_btn(self, class_name):
        return self.by_class_name(class_name)

    def get_whole_file_name(self, class_name):
        return self.by_class_name(class_name)

    def get_fragment_file_name(self, class_name):
        return self.by_class_name(class_name)

    def success_mark(self, class_name):
        return self.by_class_name(class_name)


class GeetestGetter(ElementGetter):
    def __init__(self, driver):
        self.fragment_class = 'geetest_canvas_slice'
        self.whole_class = 'geetest_canvas_bg'
        super(GeetestGetter, self).__init__(driver)

    def by_class_name(self, class_name):
        return super(GeetestGetter, self).by_class_name(class_name)

    def get_popup_btn(self):
        return self.by_class_name('geetest_radar_btn')

    def get_slider_btn(self):
        return self.by_class_name('geetest_slider_button')

    def get_refresh_btn(self):
        return self.by_class_name('geetest_refresh_1')

    def success_mark(self):
        return self.by_class_name('geetest_flash')

    def get_whole_file_name(self):
        self.by_class_name(self.fragment_class)
        self.driver.execute_script(
            'document.getElementsByClassName("'+self.fragment_class+'")[0].style.position = "static"')
        wholeImg = self.by_class_name(self.whole_class)
        wholeImg.screenshot('wholeP.png')

        self.driver.execute_script(
            'document.getElementsByClassName("'+self.fragment_class+'")[0].style.position = "absolute"')
        self.transform_whole()
        return 'wholeP.png'
        # frag_offset_height = self.driver.execute_script(
        #     'return document.querySelector(".tobe-obfuscate-image-fragment").offsetTop')
        # transform_whole(frag_offset_height)

    def transform_whole(self):
        im = Image.open('wholeP.png').convert('RGB')
        px = im.load()
        width_max = im.width
        height_max = im.height
        for w in range(0, width_max):
            for h in range(0, height_max):
                rgb = px[w, h]
                if not in_margin(rgb, 90) or rgb[0] > 180 or rgb[1] > 180 or rgb[2] > 180:
                    px[w, h] = (255, 255, 255)
                else:
                    px[w, h] = (0, 0, 0)
        # im.save('wholeP.png')
        crop_whole(im).save('wholeP.png')


    # def match(self):
    #     origin_class = 'geetest_canvas_fullbg'
    #     origin = self.by_class_name(origin_class)
    #     shadow = self.by_class_name(self.whole_class)
    #     time.sleep(2)
    #     self.driver.execute_script(
    #         'document.getElementsByClassName("' + origin_class + '")[0].style.display = "block"')
    #     origin.screenshot('origin.png')
    #     self.driver.execute_script(
    #         'document.getElementsByClassName("' + origin_class + '")[0].style.display = "none"')
    #
    #     self.driver.execute_script(
    #         'document.getElementsByClassName("' + self.fragment_class + '")[0].style.opacity = "0"')
    #     shadow.screenshot('shadow.png')
    #     matcher = ImageMatcher('full')
    #     matcher.match('origin.png', 'shadow.png')
    def get_fragment_file_name(self):
        fragment = self.by_class_name(self.fragment_class)
        self.driver.execute_script(
            'document.getElementsByClassName("' + self.whole_class + '")[0].style.display = "none"')

        fragment.screenshot('fragment.png')

        self.driver.execute_script(
            'document.getElementsByClassName("' + self.whole_class + '")[0].style.display = "block"')
        self.transform_frag()
        return 'fragment.png'

    def transform_frag(self):
        im = Image.open('fragment.png').convert('RGB')
        px = im.load()
        width_max = im.width
        height_max = im.height
        black_list = []
        for w in range(0, width_max):
            for h in range(0, height_max):
                rgb = px[w, h]
                if rgb[0] > 240 and rgb[1] > 240 and rgb[2] > 240:
                    px[w, h] = (255,255,255)
                    continue
                if rgb[0] > 220 and rgb[1] > 220 and rgb[2] < 150:
                    px[w, h] = (0, 0, 0)
                    black_list.append((w,h))
                    continue

                if in_margin(rgb, 10):
                    px[w, h] = (255, 255, 255)
                    continue
                px[w, h] = (0, 0, 0)
                black_list.append((w, h))
                # if rgb[0] > 100 or rgb[1] > 100 or rgb[2] > 100:
                #     px[w, h] = (0, 0, 0)
                #     continue
                # else:
                #     px[w, h] = (255, 255, 255)


        # crop_frag(im).save('fragment.png')
        min_x = float("inf")
        min_y = float("inf")
        max_x = 0
        max_y = 0
        for i in range(0, len(black_list)):
            dic = black_list[i]
            x = dic[0]
            y = dic[1]
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y
        croped = im.crop((min_x, min_y, max_x, max_y))
        croped_px = croped.load()
        for w in range(0, croped.width):
            for h in range(0, croped.height):
                if w > 5 and w < croped.width - 5 and h > 5 and h < croped.height - 5:
                    croped_px[w, h] = (0, 0, 0)
        croped.save('fragment.png')
        # im.save('fragment.png')


def in_margin(data, margin):
    min_n = float("inf")
    max_n = 0
    for i in range(0, len(data)):
        if data[i] < min_n:
            min_n = data[i]
        if data[i] > max_n:
            max_n = data[i]
    _margin = max_n - min_n
    if _margin > margin:
        return False
    return True


def crop_frag(im):
    pass



def crop_whole(im, offset_height=0):
    frag_height = 80
    margin_width = 30
    width = im.width
    height = im.height
    if offset_height == 0:
        frag_height = height - 1
    box = (0 + margin_width, offset_height, width - margin_width, offset_height + frag_height)
    print('crop', box)

    return im.crop(box)


def run():
    hacker = Hack('https://www.geetest.com/demo/slide-popup.html', width_margin=20)
    driver = hacker.get_driver()
    element_getter = GeetestGetter(driver)
    hacker.run(element_getter)


if __name__ == '__main__':
    run()
    # print(random.random())