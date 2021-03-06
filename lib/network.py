import tensorflow as tf
import numpy as np

from utils import fc, deconv, unpool, layer_bn, conv, pool
import resnet_v2
slim = tf.contrib.slim

class VGGNet():
    def __init__(self, name):
        self.name = name

    def encoder(self, x_ph, isTr_ph):
        with tf.variable_scope(self.name):
            l = conv('c1', [5,5,1,64], x_ph)
            l = conv('c2', [5,5,64,64], l)
            l = layer_bn('b1', l, isTr_ph)
            l = pool(l)
            l = conv('c3', [5,5,64,128], l)
            l = conv('c4', [5,5,128,128], l)
            l = layer_bn('b2', l, isTr_ph)
            l = pool(l)
            l = conv('c5', [5,5,128,256], l)
            l = conv('c6', [5,5,256,256], l)
            l = conv('c7', [5,5,256,256], l)
            l = layer_bn('b3', l, isTr_ph)
            l = pool(l)
            l = conv('c8', [5,5,256,512], l)
            l = conv('c9', [5,5,512,512], l)
            l = conv('c10', [5,5,512,512], l)
            l = layer_bn('b4', l, isTr_ph)
            l = pool(l)
            return l

    def decoder(self, hid_feat, isTr):
        with tf.variable_scope(self.name):
            L = tf.layers.conv2d_transpose(hid_feat, 512, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 512, 3, padding='SAME')
            L = layer_bn('b5', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 512, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 256, 3, padding='SAME')
            L = layer_bn('b6', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 256, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 128, 3, padding='SAME')
            L = layer_bn('b7', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 128, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 64, 3, padding='SAME')
            L = layer_bn('b8', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 32, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 1, 3, padding='SAME')
            L = tf.nn.sigmoid(L)
            L = tf.squeeze(L)
            return L


class ResAutoEncoderTrainNet():
    def __init__(self, name, loc=None):
        self.name = name
        if not loc:
            self.model_loc = 'models/'+name+'.ckpt'
        else:
            self.model_loc = loc

    def encoder(self, x_ph, reuse=False, trainable=True):
        with tf.variable_scope(self.name):
            x_reshape = tf.tile(x_ph, [1,1,1,3])
            with slim.arg_scope(resnet_v2.resnet_arg_scope()):
                _, logits = resnet_v2.resnet_v2_101(x_reshape, 1001, is_training=True)
        return logits

    def decoder(self, hid_feat, reuse=False, trainable=True):
        with tf.variable_scope(self.name):
            L = fc('dfc1', 8*8*256, hid_feat)
            L = tf.reshape(L, [-1,8,8,256])
            L = tf.layers.conv2d_transpose(L, 256, 5, strides=2, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 128, 5, strides=2, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 64, 5, strides=2, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 32, 5, strides=2, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 16, 5, strides=2, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 1, 5, strides=2, padding='SAME')
            L = tf.nn.sigmoid(L)
            L = tf.squeeze(L)
        return L

    def decoder2(self, hid_feat, reuse=False, trainable=True):
        with tf.variable_scope(self.name):
#            L = fc('dfc1', 8*8*256, hid_feat)
#            L = tf.reshape(L, [-1,8,8,256])
#            L = unpool(hid_feat)
            isTr = tf.constant(True)
            L = tf.image.resize_bilinear(hid_feat, size=[16,16])
            L = tf.layers.conv2d_transpose(L, 1024, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 512, 3, padding='SAME')
            L = layer_bn('b1', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 512, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 256, 3, padding='SAME')
            L = layer_bn('b2', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 256, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 128, 3, padding='SAME')
            L = layer_bn('b3', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 128, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 64, 3, padding='SAME')
            L = layer_bn('b4', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 64, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 32, 3, padding='SAME')
            L = layer_bn('b5', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 32, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 1, 3, padding='SAME')
            L = tf.nn.sigmoid(L)
            L = tf.squeeze(L)
            return L

    def saver_init(self):
        model_var_lists = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                scope=self.name+'*')
        self.saver = tf.train.Saver(model_var_lists)

    def saver_save(self, sess):
        print ('save model at : ', self.model_loc)
        self.saver.save(sess, self.model_loc)

    def saver_load(self, sess):
        print ('load model from : ', self.model_loc)
        self.saver.restore(sess, self.model_loc)

    def pretrain_load(self, sess):
        model_loc = 'models/'+self.name+'_pretrained.ckpt'
        print ('load pretrained model from : ', model_loc)
        var_list = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                scope=self.name+'/resnet*')
        saver = tf.train.Saver(var_list)
        saver.restore(sess, model_loc)

class ResOld(ResAutoEncoderTrainNet):
    def __init__(self, name):
        self.name = name

    def encoder(self, x_ph, reuse=False, trainable=True):
        x_reshape = tf.tile(x_ph, [1,1,1,3])
        with slim.arg_scope(resnet_v2.resnet_arg_scope()):
            logits, _ = resnet_v2.resnet_v2_101(x_reshape, 1001, is_training=True)
        return logits

    def pretrain_load(self, sess):
        pretrain_loc = '/home/aitrics/user/mike/DataSet/pretrained_model/'
        version = 'resnet_v2_101.ckpt'
        var_list = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='resnet*')
        saver = tf.train.Saver(var_list)
        saver.restore(sess, pretrain_loc+version)
        print ('pretrained model restored from : ', version)

class ResAutoEncoderTestNet(ResAutoEncoderTrainNet):
    def __init__(self, name, loc=None):
        self.name = name
        if not loc:
            self.model_loc = 'models/'+name+'.ckpt'
        else:
            self.model_loc = loc


    def encoder(self, x_ph, reuse=False, trainable=False):
        with tf.variable_scope(self.name):
            x_reshape = tf.tile(x_ph, [1,1,1,3])
            with slim.arg_scope(resnet_v2.resnet_arg_scope()):
                _, logits = resnet_v2.resnet_v2_101(x_reshape, 1001, is_training=False)
        return logits

    def decoder2(self, hid_feat, reuse=False, trainable=True):
        with tf.variable_scope(self.name):
#            L = fc('dfc1', 8*8*256, hid_feat)
#            L = tf.reshape(L, [-1,8,8,256])
#            L = unpool(hid_feat)
            isTr = tf.constant(False)
            L = tf.image.resize_bilinear(hid_feat, size=[16,16])
            L = tf.layers.conv2d_transpose(L, 1024, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 512, 3, padding='SAME')
            L = layer_bn('b1', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 512, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 256, 3, padding='SAME')
            L = layer_bn('b2', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 256, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 128, 3, padding='SAME')
            L = layer_bn('b3', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 128, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 64, 3, padding='SAME')
            L = layer_bn('b4', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 64, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 32, 3, padding='SAME')
            L = layer_bn('b5', L, isTr)
            L = unpool(L)
            L = tf.layers.conv2d_transpose(L, 32, 3, padding='SAME')
            L = tf.layers.conv2d_transpose(L, 1, 3, padding='SAME')
            L = tf.nn.sigmoid(L)
            L = tf.squeeze(L)
            return L
