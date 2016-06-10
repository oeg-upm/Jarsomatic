import unittest
import os
from subprocess import call
import datetime
from time import sleep
import ConfigParser

from mongoengine import connect

from models import Repo

abs_tests_dir = '/home/ahmad/tests'
clone_url = 'git@github.com:ahmad88me/jarsomatic-vocab-test.git'
test_folder = clone_url.split('/')[-1][:-4]
repo = clone_url.split(':')[1][:-4]
print 'test folder: %s' % test_folder
print 'repo %s ' % repo
connect("jarsomatic")
start_setup = False

class IntegrationTest(unittest.TestCase):

    vocabularies_abs_dir = os.path.join(abs_tests_dir, test_folder, 'Vocabularies.csv')
    repo = None

    def setUp(self):
        """
            clone the test repo
            clean Vocabularies.csv in master
            push the changes
            get the run
            wait until it is completed
        :return:
        """
        if not start_setup:
            return
        start_time = datetime.datetime.now()
        print 'start time: '+str(start_time)
        config_file = 'jarsomatic.cfg'
        config = ConfigParser.ConfigParser()
        if not os.path.isfile(os.path.join(app_home, config_file)):
            print "\n*** The file: "+config_file+" is not here or is not accessible ***\n"
        config.read(os.path.join(app_home, config_file))
        github_token = config.get('GITHUB', 'token')

        comm = 'cd %s; rm -Rf %s ; git clone %s ' % (abs_tests_dir, test_folder, clone_url)
        print "cloning command: "+comm
        call(comm, shell=True)
        f = open(self.vocabularies_abs_dir, 'w')
        f.write('')
        f.close()
        comm = 'cd %s; git add .; git commit -m "tests cleaning step"; git push origin master ' % os.path.join(abs_tests_dir, test_folder)
        print "cleaning command: "+comm
        call(comm, shell=True)
        for i in xrange(5):
            latest_repo = Repo.objects.all().order_by('-started_at')[0]
            if latest_repo.started_at >= start_time:
                self.repo = latest_repo
                break
            else:
                print 'keep waiting...'
                print latest_repo.started_at
                sleep(5)
        print 'preparation is done'

    def tearDown(self):
        pass

    def test_1(self):
        pass

    def test_vocab_3_repos(self):
        start_time = datetime.datetime.now()
        print '%s start time: %s' % ('test_vocab_3_repos', str(start_time))
        s = 'VocabURI;domain'
        s += '\nhttp://purl.org/net/p-plan;e-Science,plan,provenance,scientific workflow'
        s += '\nhttp://purl.org/net/wf-motifs;e-Science,workflow abstraction'
        s += '\nhttp://purl.org/net/wf-invocation;e-Science,infrastructure,scientific workflow'
        f = open(self.vocabularies_abs_dir, 'w')
        f.write(s)
        f.close()
        comm = "cd %s ; git add .; git commit -m 'automated test 3'; git push;" % (os.path.join(abs_tests_dir, test_folder))
        # print 'pushing new vocabularies: '+comm
        call(comm, shell=True)
        found = False
        for i in xrange(5):
            latest_repo = Repo.objects.all().order_by('-started_at')[0]
            if latest_repo.started_at >= start_time:
                found = True
                break
            else:
                print '%s keep waiting...' % 'test_vocab_3_repos'
                print latest_repo.started_at
                sleep(5)
        assert found, 'Took too long and yet, nothing in the list of repos.'
        print latest_repo.started_at
        print latest_repo.name
        while latest_repo.progress != 100:
            sleep(5)
            latest_repo = Repo.objects.all().order_by('-started_at')[0]
            print latest_repo.progress


if __name__ == '__main__':
    start_setup = True  # so the test only run in the case of being called
    unittest.main()
