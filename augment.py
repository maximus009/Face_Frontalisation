from PIL import Image
import numpy as np
import random
import sys, os, cv2

DLIB_PATH = '/home/sivaraman/dev/dlib-18.17/'
sys.path.append(DLIB_PATH)
import dlib

def augment(image, face, IoU_thresh = 0.75):
  ctr = 0
  for i in range(0,image.shape[0]/2,face.height()/10):
    for j in range(0,image.shape[1]/2,face.width()/10):
      bottom = face.height() - face.top()
      right = face.width() - face.left()
      dummy = dlib.rectangle(left = face.left()-j, top = face.top()-i, right =
          face.right()-j, bottom = face.bottom()-i)
      intersection = face.intersect(dummy)
      if intersection.area() > IoU_thresh * face.area():
        #cv2.rectangle(image,
            #(dummy.left(),dummy.top()),(dummy.right(),dummy.bottom()),(255,0,0),1)
        cv2.imwrite(str(ctr)+"_crop.jpg",image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1])
        ctr+=1
        cv2.imwrite(str(ctr)+"_crop.jpg",cv2.flip(image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1],1))
        ctr+=1

  for i in range(0,image.shape[0]/2,face.height()/10):
    for j in range(0,image.shape[1]/2,face.width()/10):
      bottom = face.height() - face.top()
      right = face.width() - face.left()
      dummy = dlib.rectangle(left = face.left()+j, top = face.top()-i, right =
          face.right()+j, bottom = face.bottom()-i)
      intersection = face.intersect(dummy)
      if intersection.area() > IoU_thresh * face.area():
        #cv2.rectangle(image,
            #(dummy.left(),dummy.top()),(dummy.right(),dummy.bottom()),(255,255,255),1)
        cv2.imwrite(str(ctr)+"_crop.jpg",image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1])
        ctr+=1
        cv2.imwrite(str(ctr)+"_crop.jpg",cv2.flip(image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1],
            1))
        ctr+=1

  for i in range(0,image.shape[0]/2,face.height()/10):
    for j in range(0,image.shape[1]/2,face.width()/10):
      bottom = face.height() - face.top()
      right = face.width() - face.left()
      dummy = dlib.rectangle(left = face.left()+j, top = face.top()+i, right =
          face.right()+j, bottom = face.bottom()+i)
      intersection = face.intersect(dummy)
      if intersection.area() > IoU_thresh * face.area():
        #cv2.rectangle(image,
            #(dummy.left(),dummy.top()),(dummy.right(),dummy.bottom()),(255,0,255),1)
        cv2.imwrite(str(ctr)+"_crop.jpg",image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1])
        ctr+=1
        cv2.imwrite(str(ctr)+"_crop.jpg",cv2.flip(image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1],1))
        ctr+=1

  for i in range(0,image.shape[0]/2,face.height()/10):
    for j in range(0,image.shape[1]/2,face.width()/10):
      bottom = face.height() - face.top()
      right = face.width() - face.left()
      dummy = dlib.rectangle(left = face.left()-j, top = face.top()+i, right =
          face.right()-j, bottom = face.bottom()+i)
      intersection = face.intersect(dummy)
      if intersection.area() > IoU_thresh * face.area():
        #cv2.rectangle(image,
            #(dummy.left(),dummy.top()),(dummy.right(),dummy.bottom()),(255,255,0),1)
        cv2.imwrite(str(ctr)+"_crop.jpg",image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1])
        ctr+=1
        cv2.imwrite(str(ctr)+"_crop.jpg",cv2.flip(image[dummy.top():dummy.bottom()+1,dummy.left():dummy.right()+1],1))
        ctr+=1
  
def test(image):
    face_detector = dlib.get_frontal_face_detector()
    detected_faces = face_detector(image,1)

    for face in detected_faces:
      augment(image,face, 0.8)

if __name__=="__main__":
    test(cv2.imread(sys.argv[1]))




