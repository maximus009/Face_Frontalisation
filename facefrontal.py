import scipy.misc as sm
import numpy as np
import cv2
import dlib
import pickle as pkl
import time
from scipy import ndimage
import copy
import sys

class frontalizer():
    def __init__(self,refname):
        # initialise the model with the 3d reference face 
        # and the camera intrinsic parameters 
        # they are stored in the ref3d.pkl  
        with open(refname) as f:
            ref = pkl.load(f)
            self.refU  = ref['refU']
            self.A = ref['outA']
            self.refxy = ref['ref_XY']
            self.p3d = ref['p3d']
            self.refimg = ref['refimg']
    def get_headpose(self,p2d):
        assert(len(p2d) == len(self.p3d))
        p3_ = np.reshape(self.p3d,(-1,3,1)).astype(np.float)
        p2_ = np.reshape(p2d,(-1,2,1)).astype(np.float)
        distCoeffs = np.zeros((5,1))
        succ,rvec,tvec = cv2.solvePnP(p3_,p2_, self.A, distCoeffs)
        if not succ:
            print 'There is something wrong, please check.'
            return None
        else:
            matx = cv2.Rodrigues(rvec)
            ProjM_ = self.A.dot(np.insert(matx[0],3,tvec.T,axis=1))
            return rvec,tvec,ProjM_
    def frontalization(self,img_,facebb,p2d_):
        #we rescale the face region (twice as big as the detected face) before applying frontalisation
        #the rescaled size is WD x HT 
        WD = 250 
        HT = 250 
        ACC_CONST = 800
        facebb = [facebb.left(), facebb.top(), facebb.width(), facebb.height()]
        w = facebb[2]
        h = facebb[3]
        fb_ = np.clip([[facebb[0] - w, facebb[1] - h],[facebb[0] + 2 * w, facebb[1] + 2 * h]], [0,0], [img_.shape[1], img_.shape[0]])  
        img = img_[fb_[0][1]:fb_[1][1], fb_[0][0]:fb_[1][0],:]
        p2d = copy.deepcopy(p2d_) 
        p2d[:,0] = (p2d_[:,0] - fb_[0][0]) * float(WD) / float(img.shape[1])
        p2d[:,1] = (p2d_[:,1] - fb_[0][1])  * float(HT) / float(img.shape[0])
        img = cv2.resize(img, (WD,HT)) 
        #finished rescaling
        #sm.toimage(np.round(img).astype(np.uint8)).show()
        #
       
        tem3d = np.reshape(self.refU,(-1,3),order='F')
        bgids = tem3d[:,1] < 0# excluding background 3d points 
        #plot3d(tem3d)
        ref3dface = np.insert(tem3d, 3, np.ones(len(tem3d)),axis=1).T
        #print tem3d.shape 
        ProjM = self.get_headpose(p2d)[2]
        proj3d = ProjM.dot(ref3dface)
        proj3d[0] /= proj3d[2] 
        proj3d[1] /= proj3d[2]
        proj2dtmp = proj3d[0:2]
        #The 3D reference is projected to the 2D region by the estimated pose 
        #The check the projection lies in the image or not 
        vlids = np.logical_and(np.logical_and(proj2dtmp[0] > 0, proj2dtmp[1] > 0), 
                               np.logical_and(proj2dtmp[0] < img.shape[1] - 1,  proj2dtmp[1] < img.shape[0] - 1))
        vlids = np.logical_and(vlids, bgids)
        proj2d_valid = proj2dtmp[:,vlids]

        sp_  = self.refU.shape[0:2]
        synth_front = np.zeros(sp_,np.float)
        inds = np.ravel_multi_index(np.round(proj2d_valid).astype(int),(img.shape[1], img.shape[0]),order = 'F')
        

        #unqeles, unqinds, inverids, conts  = np.unique(inds,return_index=True,return_inverse=True, return_counts=True)
        unqeles, unqinds, inverids = np.unique(inds, return_index=True, return_inverse=True)
        freq = np.bincount(inverids)
        conts = np.array([unqeles, freq]).T
        tmp_ = synth_front.flatten()
        tmp_[vlids] = conts[inverids].astype(np.float)
        synth_front = tmp_.reshape(synth_front.shape,order='F')
        synth_front = cv2.GaussianBlur(synth_front, (17,17), 30).astype(np.float)

        rawfrontal = np.zeros((self.refU.shape[0],self.refU.shape[1], 3)) 
        for k in range(3):
            z = img[:,:,k]
            intervalues = ndimage.map_coordinates(img[:,:,k].T,proj2d_valid,order=3,mode='nearest')
            tmp_  = rawfrontal[:,:,k].flatten()
            tmp_[vlids] = intervalues
            rawfrontal[:,:,k] = tmp_.reshape(self.refU.shape[0:2],order='F')

        mline = synth_front.shape[1]/2
        sumleft = np.sum(synth_front[:,0:mline])
        sumright = np.sum(synth_front[:,mline:])
        sum_diff = sumleft - sumright
        #print sum_diff
        if np.abs(sum_diff) > ACC_CONST:
            weights = np.zeros(sp_)
            if sum_diff > ACC_CONST:
                weights[:,mline:] = 1.
            else:
                weights[:,0:mline] = 1.
            weights = cv2.GaussianBlur(weights, (33,33), 60.5).astype(np.float)
            synth_front /= np.max(synth_front) 
            weight_take_from_org = 1 / np.exp(1 + synth_front)
            weight_take_from_sym = 1 - weight_take_from_org
            weight_take_from_org = weight_take_from_org * np.fliplr(weights)
            weight_take_from_sym = weight_take_from_sym * np.fliplr(weights) 
            weights = np.tile(weights,(1,3)).reshape((weights.shape[0],weights.shape[1],3),order='F')
            weight_take_from_org = np.tile(weight_take_from_org,(1,3)).reshape((weight_take_from_org.shape[0],weight_take_from_org.shape[1],3),order='F')
            weight_take_from_sym = np.tile(weight_take_from_sym,(1,3)).reshape((weight_take_from_sym.shape[0],weight_take_from_sym.shape[1],3),order='F')
            denominator = weights + weight_take_from_org + weight_take_from_sym
            frontal_sym = (rawfrontal * weights + rawfrontal * weight_take_from_org + np.fliplr(rawfrontal) * weight_take_from_sym) / denominator
        else:
            frontal_sym = rawfrontal
        print facebb
        return rawfrontal, frontal_sym, img

if __name__ == "__main__":

    #ctr = 0
    ##to make sure you have dlib 
    PATH_face_model = 'face_shape.dat'
    md_face = dlib.shape_predictor(PATH_face_model)
    face_det = dlib.get_frontal_face_detector()
    fronter = frontalizer('ref3d.pkl')
    # test your image
    img_name = sys.argv[1]
    img = plt.imread(img_name)
    facedets = face_det(img,1)
    k = 1
    
    for det in facedets:
        shape = md_face(img,det)
        p2d = np.asarray([(shape.part(n).x, shape.part(n).y,) for n in range(shape.num_parts)], np.float32)
        st = time.time()
        # Location of the left tip, right tip and the tip of the nose.
        (xr,yr),(xc, yc), (xl,yl) = p2d[0],p2d[33],p2d[16]
        rawfront, symfront, orig_face = fronter.frontalization(img,det,p2d)
        
        orig_face = np.array(sm.toimage(np.round(orig_face).astype(np.uint8)))
        #To check if face is turned left or right and crop only the visible half
        if ((xc-xr)**2+(yc-yr)**2)>((xc-xl)**2+(yc-yl)**2):
            #RIGHT
            half = np.array(sm.toimage(np.round(symfront).astype(np.uint8)))[55:251,77:156]
        else:
            half = cv2.flip(np.array(sm.toimage(np.round(symfront).astype(np.uint8))),1)[55:251,77:156]

        print "eplased time:", time.time() - st 
        sm.imsave("all_results/"+img_name.split('.')[0].split('/')[-1]+"_"+str(k)+".jpg",np.hstack((cv2.resize(orig_face,(320,320)),np.array(sm.toimage(np.round(symfront).astype(np.uint8))))))
        sm.imsave("just_front/"+img_name.split('.')[0].split('/')[-1]+"_"+str(k)+".jpg",np.array(sm.toimage(np.round(symfront).astype(np.uint8)))[55:251,77:234])
        sm.imsave("just_half/"+img_name.split('.')[0].split('/')[-1]+"_"+str(k)+".jpg",half)
        k+=1
