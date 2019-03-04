import argparse
import numpy as np
import tensorflow as tf
from utils import *
#testing
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


GRAPH = 'retrained_graph.pb'
with open('labels.txt', 'r') as f:
    LABELS = f.read().split()

def compute_brute_force_classification(image_path, nH=8, nW=8):
    '''
    This function returns the probabilities of each window.
    Inputs:
        image_path: path to the image to be analysed
        nH: number of windows in the vertical direction
        nW: number of windows in the horizontal direction
    Outputs:
        window_predictions: a (nH, nW, 3) np.array. 
                            The last dim (size 3) is the probabilities 
                            of each label (cat, dog, neg)
    HINT: classify_image  (from utils.py) will be useful here. 
    HINT: You will need to define a tensorflow session. You can do this by running:
          with tf.Session() as sess: 
    '''
    ######### Your code ends here #########
    # H x W x 3 numpy array (3 for each RGB color channel)
    raw_image = decode_jpeg(image_path)
    #image size
    H=raw_image.shape[0]
    W=raw_image.shape[1]
    rgb=raw_image.shape[2]

    ylength=H/nH
    xlength=W/nW
    stepsize= 100 #pixels the less value the refined, but more computation
    paddingbefore=stepsize
    paddingafter=stepsize
    npad = ((paddingbefore, paddingafter), (paddingbefore, paddingafter), (0, 0)) ## npad is a tuple of (n_before, n_after) for each dimension
    #I am adding 20 pixels after and before for my padding. Account for this in dfor loop in both x and y
    imagepad=np.pad(raw_image, npad, mode='constant', constant_values=0)
    extrapad=paddingbefore+paddingafter

    window_predictions=np.zeros((nH,nW,rgb))

    with tf.Session() as sess:

        for y in range(nH):
            for x in range(nW):
                #account for extra padding stepsize before and after with extrapad
                window = imagepad[y*ylength:(y+1)*ylength+extrapad, x*xlength:(x+1)*xlength+extrapad,:]
                window_predictions[y,x,:] = classify_image(window, sess)
                print("xgrid,ygrid=",x,y)
                if x and y == nH:
                    break

   ######### Your code ends here #########
                
    return window_predictions #shape (8,8,3) size 192

def compute_convolutional_KxK_classification(image):
    graph = tf.get_default_graph()
    classification_input_tensor =  graph.get_tensor_by_name('bottleneck_input/BottleneckInputPlaceholder:0')
    classification_output_tensor = graph.get_tensor_by_name('final_result:0')
    convolution_ouput_tensor = graph.get_tensor_by_name('bottleneck_grid:0')    # 'mixed_10/join:0' in Inception-v3
    K = convolution_ouput_tensor.shape[0]

    with tf.Session() as sess:
        convolution_output = run_with_image_input(convolution_ouput_tensor, image, sess)
        predictionsKxK = sess.run(classification_output_tensor,
                                  {classification_input_tensor: np.reshape(convolution_output, [K*K, -1])})
        return np.reshape(predictionsKxK, [K,K,-1])

def compute_and_plot_saliency(image):
    '''
    This function computes and plots the saliency plot.
    Input: image to be analysed
    Output: None

    You need to compute the matrix M detailed in section 3.1 in
    K. Simonyan, A. Vedaldi, and A. Zisserman, 
    "Deep inside convolutional networks: Visualising imageclassification models and saliency maps," 
    2013, Available at https://arxiv.org/abs/1312.6034.
    '''
    graph = tf.get_default_graph()
    logits_tensor = graph.get_tensor_by_name('final_training_ops/Wx_plus_b/logits:0')

    with tf.Session() as sess:
        logits = np.squeeze(run_with_image_input(logits_tensor, image, sess))
        top_class = np.argmax(logits)
        w_ijc = gradient_of_class_score_with_respect_to_input_image(image, top_class, sess)    # defined in utils.py
    ######### Your code starts here #########
    # M = np.zeros(raw_gradients.shape[0:2])  # something of the right shape to plot
        M=np.ndarray.max(w_ijc,axis=2) #max i and j along third dimesion

    ######### Your code ends here #########

    plt.subplot(2,1,1)
    plt.imshow(M)
    plt.title('Saliency with respect to predicted class %s' % LABELS[top_class])
    plt.subplot(2,1,2)
    plt.imshow(decode_jpeg(image))
    plt.show()

def plot_classification(image_path, classification_array):
    nH, nW, _ = classification_array.shape
    image_data = decode_jpeg(image_path)
    aspect_ratio = float(image_data.shape[0]) / image_data.shape[1]
    plt.figure(figsize=(8, 8*aspect_ratio))
    p1 = plt.subplot(2,2,1)
    plt.imshow(classification_array[:,:,0], interpolation='none', cmap='jet')
    plt.title('%s probability' % LABELS[0])
    p1.set_aspect(aspect_ratio*nW/nH)
    plt.colorbar()
    p2 = plt.subplot(2,2,2)
    plt.imshow(classification_array[:,:,1], interpolation='none', cmap='jet')
    plt.title('%s probability' % LABELS[1])
    p2.set_aspect(aspect_ratio*nW/nH)
    plt.colorbar()
    p2 = plt.subplot(2,2,3)
    plt.imshow(classification_array[:,:,2], interpolation='none', cmap='jet')
    plt.title('%s probability' % LABELS[2])
    p2.set_aspect(aspect_ratio*nW/nH)
    plt.colorbar()
    plt.subplot(2,2,4)
    plt.imshow(image_data)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str)
    parser.add_argument('--scheme', type=str)
    FLAGS, _ = parser.parse_known_args()

    load_graph(GRAPH)
    
    #use for debugging
    # image_path=mpimg.imread('/home/aa274/catkin_ws/src/AA274_HW2/Problem_4/datasets/catswithdogs/002034.jpg')
    # compute_brute_force_classification(image_path, nH=8, nW=8)
    # compute_and_plot_saliency(image_path)

    if FLAGS.scheme == 'brute':
        plot_classification(FLAGS.image, compute_brute_force_classification(FLAGS.image, 8, 8))
    elif FLAGS.scheme == 'conv':
        plot_classification(FLAGS.image, compute_convolutional_KxK_classification(FLAGS.image))
    elif FLAGS.scheme == 'saliency':
        compute_and_plot_saliency(FLAGS.image)
    else:
        print 'Unrecognized scheme:', FLAGS.scheme