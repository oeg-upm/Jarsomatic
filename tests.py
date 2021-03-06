import unittest
import os
from subprocess import call
import datetime
from time import sleep
import ConfigParser
import requests
from github import Github

from mongoengine import connect

from models import Repo

# abs_tests_dir = '/home/ahmad/tests'
clone_url = 'git@github.com:ahmad88me/jarsomatic-vocab-test.git'
test_folder = clone_url.split('/')[-1][:-4]
repo = clone_url.split(':')[1][:-4]
print 'test folder: %s' % test_folder
print 'repo %s ' % repo
connect("jarsomatic")
start_setup = False


class IntegrationTest(unittest.TestCase):

    # vocabularies_abs_dir = os.path.join(abs_tests_dir, test_folder, 'Vocabularies.csv')
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
        app_home = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isfile(os.path.join(app_home, config_file)):
            print "\n*** The file: "+config_file+" is not here or is not accessible ***\n"
        config.read(os.path.join(app_home, config_file))
        self.abs_tests_dir = config.get('DEFAULT', 'tmp')
        self.vocabularies_abs_dir = os.path.join(self.abs_tests_dir, test_folder, 'Vocabularies.csv')
        print 'vocabularies dir: '+self.vocabularies_abs_dir
        github_token = config.get('GITHUB', 'token')
        self.g = Github(github_token)
        comm = "git config --global user.email 'jarsomatic@delicias.dia.fi.upm.es' ; "
        comm += "git config --global user.name 'Test' ; "
        call(comm, shell=True)
        comm = 'cd %s; rm -Rf %s ; git clone %s ' % (self.abs_tests_dir, test_folder, clone_url)
        print "cloning command: "+comm
        call(comm, shell=True)
        f = open(self.vocabularies_abs_dir, 'w')
        f.write('')
        f.close()
        comm = 'cd %s; git add .; git commit -m "tests cleaning step"; git push origin master ' % \
               os.path.join(self.abs_tests_dir, test_folder)
        print "cleaning command: "+comm
        call(comm, shell=True)
        sleep(30)
        latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
        while latest_repo['progress'] != 100:
            print 'clear - keep waiting...'
            print latest_repo['started_at']
            sleep(15)
            latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
        print 'preparation is done'

    def tearDown(self):
        pass

    def test_1(self):
        pass

    def test_vocab_3_repos(self):
        pass
        comm = "git config --global user.email 'jarsomatic@delicias.dia.fi.upm.es' ; "
        comm += "git config --global user.name 'Test3' ; "
        call(comm, shell=True)
        start_time = datetime.datetime.now()
        print '%s start time: %s' % ('test_vocab_3_repos', str(start_time))
        s = 'VocabURI;domain'
        s += '\nhttp://purl.org/net/p-plan;e-Science,plan,provenance,scientific workflow'
        s += '\nhttp://purl.org/net/wf-motifs;e-Science,workflow abstraction'
        s += '\nhttp://purl.org/net/wf-invocation;e-Science,infrastructure,scientific workflow'
        f = open(self.vocabularies_abs_dir, 'w')
        f.write(s)
        f.close()
        comm = "cd %s ; git add . ; git commit -m 'automated test 3'; git push;" % \
               os.path.join(self.abs_tests_dir, test_folder)
        call(comm, shell=True)
        sleep(30)
        latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
        print latest_repo['started_at']
        print latest_repo['name']
        while latest_repo['progress'] != 100:
            sleep(15)
            latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
            print 'test3: '+str(latest_repo['progress'])
        original_repo = 'jarsomatic/'+repo.split('/')[1]
        print 'original repo: '+original_repo
        r = self.g.get_repo(original_repo)
        print 'get repo'
        c = r.get_file_contents('site/index.html', 'gh-pages').decoded_content
        print 'gotten the content'
        response = c
        assert len(response.split('<tr id')) == 4, 'Number of vocabularies does not match'
        assert 'p-plan' in response, 'p-plan is not in the index.html'
        assert 'wf-motifs' in response, 'wf-motifs is not in index.html'
        assert 'wf-invocation' in response, 'wf-invocation is not in index.html'

    def test_vocab_4_repos(self):
            comm = "git config --global user.email 'jarsomatic@delicias.dia.fi.upm.es' ; "
            comm += "git config --global user.name 'Test4' ; "
            call(comm, shell=True)
            start_time = datetime.datetime.now()
            print '%s start time: %s' % ('test_vocab_4_repos', str(start_time))
            s = 'VocabURI;domain'
            s += '\nhttp://purl.org/net/p-plan;e-Science,plan,provenance,scientific workflow'
            s += '\nhttp://purl.org/net/wf-motifs;e-Science,workflow abstraction'
            s += '\nhttp://purl.org/net/wf-invocation;e-Science,infrastructure,scientific workflow'
            s += '\nhttp://purl.org/net/ro-optimization;e-Science,Research Object'
            f = open(self.vocabularies_abs_dir, 'w')
            f.write(s)
            f.close()
            comm = "cd %s ; git add . ; git commit -m 'automated test 4'; git push;" % \
                   os.path.join(self.abs_tests_dir, test_folder)
            call(comm, shell=True)
            sleep(30)
            latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
            print latest_repo['started_at']
            print latest_repo['name']
            while latest_repo['progress'] != 100:
                sleep(15)
                latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
                print 'test4: '+str(latest_repo['progress'])
            original_repo = 'jarsomatic/'+repo.split('/')[1]
            print 'original repo: '+original_repo
            r = self.g.get_repo(original_repo)
            print 'get repo'
            c = r.get_file_contents('site/index.html', 'gh-pages').decoded_content
            print 'gotten the content'
            response = c
            assert len(response.split('<tr id')) == 5, 'Number of vocabularies does not match'
            assert 'p-plan' in response, 'p-plan is not in the index.html'
            assert 'wf-motifs' in response, 'wf-motifs is not in index.html'
            assert 'wf-invocation' in response, 'wf-invocation is not in index.html'
            assert 'ro-optimization' in response, 'ro-optimization is not in index.html'

    def test_vocab_5_repos(self):
            comm = "git config --global user.email 'jarsomatic@delicias.dia.fi.upm.es' ; "
            comm += "git config --global user.name 'Test5' ; "
            call(comm, shell=True)
            start_time = datetime.datetime.now()
            print '%s start time: %s' % ('test_vocab_5_repos', str(start_time))
            s = 'VocabURI;domain'
            s += '\nhttp://purl.org/net/p-plan;e-Science,plan,provenance,scientific workflow'
            s += '\nhttp://purl.org/net/wf-motifs;e-Science,workflow abstraction'
            s += '\nhttp://purl.org/net/wf-invocation;e-Science,infrastructure,scientific workflow'
            s += '\nhttp://purl.org/net/ro-optimization;e-Science,Research Object'
            s += '\nhttp://purl.org/net/wf-fd;e-Science,workflow abstraction'
            f = open(self.vocabularies_abs_dir, 'w')
            f.write(s)
            f.close()
            comm = "cd %s ; git add . ; git commit -m 'automated test 5'; git push;" % \
                   os.path.join(self.abs_tests_dir, test_folder)
            call(comm, shell=True)
            sleep(30)
            latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
            print latest_repo['started_at']
            print latest_repo['name']
            while latest_repo['progress'] != 100:
                sleep(15)
                latest_repo = requests.get('http://jarsomatic.linkeddata.es/get_latest_repo').json()
                print 'test5: '+str(latest_repo['progress'])
            original_repo = 'jarsomatic/'+repo.split('/')[1]
            print 'original repo: '+original_repo
            r = self.g.get_repo(original_repo)
            print 'get repo'
            c = r.get_file_contents('site/index.html', 'gh-pages').decoded_content
            print 'gotten the content'
            response = c
            assert len(response.split('<tr id')) == 6, 'Number of vocabularies does not match'
            assert 'p-plan' in response, 'p-plan is not in the index.html'
            assert 'wf-motifs' in response, 'wf-motifs is not in index.html'
            assert 'wf-invocation' in response, 'wf-invocation is not in index.html'
            assert 'ro-optimization' in response, 'ro-optimization is not in index.html'
            assert 'wf-fd' in response, 'wf-fd is not in index.html'


if __name__ == '__main__':
    start_setup = True  # so the test only run in the case of being called
    unittest.main()
