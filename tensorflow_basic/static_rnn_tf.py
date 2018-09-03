# -*- coding:utf-8 -*-

# ==============================================================================
# tensorflow循环神经网络结构。recurrent neural network
# ==============================================================================
import tensorflow as tf
import os
import config.common_config as com_config
from tensorflow.examples.tutorials.mnist import input_data
from util.log_util import LoggerUtil
from util.tensorflow_util import TensorFlowUtil

# 日志器
common_logger = LoggerUtil.get_common_logger()
# mnist数据
mnist = input_data.read_data_sets(com_config.MNIST_DIR, one_hot=True)
n_input = 784  # MNIST data input (img shape: 28*28)
n_classes = 10  # MNIST total classes (0-9 digits)


class StaticRNN(object):
    """
    静态循环神经网络。
    """
    def __init__(self, input_dim, output_dim):
        """
        初始化网络数据
        :param input_dim:
        :param output_dim:
        """
        # 网络结构参数
        self.x_input = None
        self.y_label = None
        self.weight = None
        self.bias = None
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_input = 28
        self.time_steps = 28
        self.num_hidden = 128

        # 训练需要的超参数
        self.learning_rate = 1e-2
        self.training_epochs = 20
        self.batch_size = 128
        self.display_steps = 20
        self.save_steps = 20

        # 预测优化函数
        self.y_predict = None
        self.y_value = None
        self.loss = None
        self.accuracy = None
        self.optimizer = None

        # sess会话
        self.sess = None

        # 初始化器
        self.initializer = None
        self.merged_summary_op = None

        # 目录初始化
        self.tf_logs_path = os.path.join(com_config.TF_MODEL_LOGS_DIR, "staticRNN")
        self.checkpoints_path = os.path.join(com_config.TF_MODEL_CHECKPOINT_DIR, "staticRNN")

        # 变量和参数初始化
        self.init_network()

    @staticmethod
    def name():
        """
        网络结构名称。
        :return:
        """
        return "Static Recurrent Neural Network(StaticRNN)"

    def init_network(self):
        """
        初始化网络结构信息。
        :return:
        """
        self.placeholders()
        self.variables()
        self.inference()
        self.loss_function()
        self.evaluate_function()
        self.summary()
        self.solver()
        # 初始化变量的操作应该放在最后
        self.init_variables()

    def placeholders(self):
        """
        使用到的占位符。
        :return:
        """
        # 模型的输入x值
        self.x_input = tf.placeholder(tf.float32, [None, self.input_dim], name="x_input")
        # 模型的输入y值
        self.y_label = tf.placeholder(tf.float32, [None, self.output_dim], name="y_label")

    def variables(self):
        """
        使用到的变量。
        :return:
        """
        self.weight = TensorFlowUtil.weight_variable([self.num_hidden, self.output_dim])
        self.bias = TensorFlowUtil.bias_variable([self.output_dim])

    def init_variables(self):
        """
        初始化变量。
        :return:
        """
        self.initializer = tf.global_variables_initializer()

    def inference(self):
        """
        网络结构生成。
        :return:
        """
        # 计算预测值
        x_images = tf.reshape(self.x_input, shape=[-1, self.time_steps, self.num_input])
        x_stack = tf.unstack(x_images, self.time_steps, 1)
        lstm_cell = tf.contrib.rnn.BasicLSTMCell(self.num_hidden, forget_bias=1.0)
        outputs, states = tf.contrib.rnn.static_rnn(lstm_cell, x_stack, dtype=tf.float32)
        self.y_value = tf.matmul(outputs[-1], self.weight) + self.bias
        self.y_predict = tf.nn.softmax(self.y_value)

    def loss_function(self):
        """
        损失函数设置。
        :return:
        """
        # 1. 计算softmax交叉熵
        softmax_cross_entropy = tf.nn.softmax_cross_entropy_with_logits_v2(labels=self.y_label, logits=self.y_value)
        self.loss = tf.reduce_mean(tf.reduce_sum(softmax_cross_entropy))

    def evaluate_function(self):
        """
        评价函数设置。
        :return:
        """
        self.accuracy = tf.equal(tf.argmax(self.y_predict, 1), tf.argmax(self.y_label, 1))
        self.accuracy = tf.reduce_mean(tf.cast(self.accuracy, tf.float32))

    def solver(self):
        """
        求解器。
        :return:
        """
        # 1. Gradient Descent
        # self.optimizer = tf.train.GradientDescentOptimizer(self.learning_rate).minimize(self.loss)
        # 2. Adam
        self.optimizer = tf.train.AdamOptimizer(self.learning_rate).minimize(self.loss)

    def summary(self):
        """
        summary 网络结构运行状况概要。
        :return:
        """
        tf.summary.scalar("loss", self.loss)
        self.merged_summary_op = tf.summary.merge_all()

    def train(self):
        """
        训练网络参数。
        :return:
        """
        with tf.Session() as sess:
            self.sess = sess
            # 初始化
            sess.run(self.initializer)
            # 训练数据

    def train_mnist(self):
        """
        训练mnist数据
        :return:
        """
        with tf.Session() as sess:
            self.sess = sess
            # 执行初始化
            sess.run(self.initializer)
            # summary writer
            summary_writer = tf.summary.FileWriter(self.tf_logs_path,
                                                   graph=tf.get_default_graph())
            # saver
            saver = tf.train.Saver()

            # 训练数据
            for epoch in range(self.training_epochs):
                avg_cost = 0.
                total_batch = int(mnist.train.num_examples / self.batch_size)
                # 循环运行所有批次数据
                for i_batch in range(total_batch):
                    batch_xs, batch_ys = mnist.train.next_batch(self.batch_size)

                    total_index = epoch * total_batch + i_batch
                    # 执行优化、损失函数、准确率
                    if i_batch % self.display_steps == 0:
                        _, cost_value, accuracy_value, summary = \
                            sess.run([self.optimizer, self.loss, self.accuracy, self.merged_summary_op],
                                     feed_dict={self.x_input: batch_xs, self.y_label: batch_ys})

                        # 在summary_writer中记录相应的训练过程
                        summary_writer.add_summary(summary, total_index)
                        # 计算平均损失
                        avg_cost += cost_value / total_batch

                        common_logger.info("Epoch: {0:0>4}_{1:0>4} cost={2:.9f} accuracy={3:.9f}"
                                           .format((epoch + 1), i_batch, cost_value, accuracy_value))
                    else:
                        sess.run(self.optimizer, feed_dict={self.x_input: batch_xs, self.y_label: batch_ys})

                # 记录每轮迭代的中间结果
                if (epoch + 1) % self.display_steps == 0:
                    common_logger.info("Epoch: {0:0>4} cost={1:.9f}".format((epoch + 1), avg_cost))
                if (epoch + 1) % self.save_steps == 0:
                    saver.save(sess, self.checkpoints_path, global_step=(epoch + 1))

            # 记录训练的最终结果
            saver.save(sess, self.checkpoints_path, global_step=(self.training_epochs + 1))
            common_logger.info("Optimization Finished!")

            # 测试模型，计算测试数据的准确率
            test_accuracy = self.accuracy.eval(
                {self.x_input: mnist.test.images, self.y_label: mnist.test.labels})

            common_logger.info("Accuracy:{0}".format(test_accuracy))

            self.show_variable()

    def show_variable(self):
        """
        输出变量的结果。
        :return:
        """
        variable_names = [v.name for v in tf.trainable_variables()]
        values = self.sess.run(variable_names)
        for k, v in zip(variable_names, values):
            common_logger.info("Variable: {0} {1}, {2}".format(k, v, v.shape))


def static_rnn_model():
    """
    静态循环神经网络模型。
    :return:
    """
    # 超参数
    learning_rate = 0.001
    training_steps = 50000
    batch_size = 128
    display_steps = 200

    # Network Parameters
    num_input = 28
    time_steps = 28
    num_hidden = 128  # hidden layer num of features
    num_classes = 10  # MNIST total classes (0-9 digits)

    # 参数和占位符
    x_input = tf.placeholder(tf.float32, [None, n_input], name="x_input")
    y_label = tf.placeholder(tf.float32, [None, num_classes], name="y_label")

    w_out = TensorFlowUtil.weight_variable([num_hidden, num_classes])
    b_out = TensorFlowUtil.bias_variable([num_classes])

    # 构建网络
    x_images = tf.reshape(x_input, shape=[-1, time_steps, num_input])
    x_stack = tf.unstack(x_images, time_steps, 1)
    lstm_cell = tf.contrib.rnn.BasicLSTMCell(num_hidden, forget_bias=1.0)
    outputs, states = tf.contrib.rnn.static_rnn(lstm_cell, x_stack, dtype=tf.float32)
    y_value = tf.matmul(outputs[-1], w_out) + b_out
    y_predict = tf.nn.softmax(y_value)

    # 损失函数和准确率
    cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=y_value, labels=y_label))
    correct_prediction = tf.equal(tf.argmax(y_predict, 1), tf.argmax(y_label, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    # 优化函数
    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(cross_entropy)

    # 执行训练
    sess = tf.InteractiveSession()
    tf.global_variables_initializer().run()
    for index in range(training_steps):
        # 分批训练
        batch_xs, batch_ys = mnist.train.next_batch(batch_size)
        if index % display_steps == 0:
            _, cost_value, accuracy_value = sess.run([train_step, cross_entropy, accuracy],
                                                     feed_dict={x_input: batch_xs, y_label: batch_ys})
            common_logger.info("Epoch: {0:0>4} cost={1:.9f} accuracy={2:.9f}"
                               .format(index, cost_value, accuracy_value))
        else:
            sess.run(train_step, feed_dict={x_input: batch_xs, y_label: batch_ys})

    # 训练数据的准确率
    train_accuracy = sess.run(accuracy, feed_dict={x_input: mnist.train.images,
                                                   y_label: mnist.train.labels})
    common_logger.info("Train Accuracy:{0:.9f}".format(train_accuracy))

    # 测试数据的准确率
    test_accuracy = sess.run(accuracy, feed_dict={x_input: mnist.test.images,
                                                  y_label: mnist.test.labels})
    common_logger.info("Test Accuracy:{0:.9f}".format(test_accuracy))


if __name__ == "__main__":
    # static_rnn_model()
    static_rnn = StaticRNN(n_input, n_classes)
    static_rnn.train_mnist()
    pass

