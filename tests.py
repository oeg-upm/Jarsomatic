import unittest
import os
from subprocess import call
import datetime
from models import Repo
from time import sleep

abs_tests_dir = '/home/ahmad/tests'
clone_url = 'git@github.com:ahmad88me/vocabUpdates.git'
test_folder = clone_url.split('/')[-1][:-4]
repo = clone_url.split(':')[1][:-4]
print 'test folder: %s' % test_folder
print 'repo %s ' % repo


class IntegrationTest(unittest.TestCase):

    def setUp(self):
        """
            clone the test repo
            clean Vocabularies.csv in master
            push the changes
            get the run
            wait until it is completed
        :return:
        """
        start_time = datetime.datetime.now()
        comm = 'cd %s; git clone %s ' % (abs_tests_dir, clone_url)
        call(comm, shell=True)
        f = open(os.path.join(abs_tests_dir, test_folder, 'Vocabularies.csv'),'w')
        f.write('')
        f.close()
        comm = 'cd %s; git push origin master ' % abs_tests_dir
        call(comm, shell=True)
        while(Repo.objects.all().order_by('-started_at')[0].started_at < start_time):
            latest_repo = Repo.objects.all().order_by('started_at')[0]
            print 'keep waiting...'
            print latest_repo.started_time
            sleep(5)
        # comm = 'cd %s; git checkout -b origin/gh-pages gh-pages ;' % abs_tests_dir
        # call(comm, shell=True)  # clone the testing repo
        # f = open(os.path.join(abs_tests_dir, test_folder, 'Vocabularies.csv'))
        # f.write('')
        # f.close()
        # sleep(5)


    def tearDown(self):
        pass

    def test1(self):
        pass

    def test2(self):
        pass

if __name__ == '__main__':
    unittest.main()