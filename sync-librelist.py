#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    sync librelist
    ~~~~~~~~~~~~~~

    Pulls in the latest version of the mails from the Flask librelist
    mailinglist and sorts them by thread into the processed folder as
    json dumps with the most relevant information.

    This will also trigger the rsync.

    :copyright: Copyright 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement

import os
import re
import unicodedata
from glob import glob
from subprocess import Popen

from flask import json
from werkzeug import Headers, parse_date
from websiteconfig import INCOMING_MAIL_FOLDER, THREAD_FOLDER, \
     LIST_NAME, RSYNC_PATH, SUBJECT_PREFIX


_punctuation_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')
_mail_split_re = re.compile(r'"?(.*?)"?(?:\s+<([^>]+)>)?$')
_string_inc_re = re.compile(r'(\d+)$')
_msgid_re = re.compile(r'<([^>]+)>')


def unquote_msgid(msgid):
    msgid = (msgid or '').strip().strip('<>')
    if msgid:
        if '@' in msgid:
            a, b = msgid.split('@', 1)
            return a.strip('"') + '@' + b
        return msgid.decode('iso-8859-15', 'replace')


def split_email(s):
    p1, p2 = _mail_split_re.match(s.strip()).groups()
    if p2:
        words = p1.split()
        for idx, word in enumerate(words):
            if word.isupper():
                words[idx] = word.capitalize()
        return u' '.join(words), p2
    elif '@' in p1:
        return None, p1
    return p1, None


def increment_string(string):
    match = _string_inc_re.search(string)
    if match is None:
        return string + u'2'
    return string[:match.start()] + unicode(int(match.group(1)) + 1)


def strip_subject_prefix(string):
    """Unstrips a title"""
    if string.startswith(SUBJECT_PREFIX):
        return string[len(SUBJECT_PREFIX):].lstrip()
    if string[:3].lower() in (u'aw:', u're:'):
        return u'Re: ' + strip_subject_prefix(string[3:].lstrip())
    if string[:3].lower() in (u'fw:', u'wg:'):
        return u'Fw: ' + strip_subject_prefix(string[3:].lstrip())
    return string


def rsync():
    """Invokes rsync"""
    Popen(['rsync', '-qazv', RSYNC_PATH % LIST_NAME,
           INCOMING_MAIL_FOLDER]).wait()


class Tree(object):

    def __init__(self, threads):
        self.threads = threads
        self.processed_mail = set()
        self._new_mail = []
        self._known_ids = {}

        def _walk_mails(mails):
            for mail in mails:
                self.processed_mail.add(mail['fsid'])
                self._known_ids[mail['msgid']] = mail
                _walk_mails(mail['children'])
        _walk_mails(x['root'] for x in threads)

    def slug_used(self, slug):
        for thread in self.threads:
            if thread['slug'] == slug:
                return True
        return False

    def generate_slug(self, mail):
        date = parse_date(mail['date'])
        if date is None:
            date = 'missing-date'
        else:
            date = date.strftime('%Y-%m-%d')
        rv = u'%s/%s' % (date,
            '-'.join(x for x in _punctuation_re.split(
                unicodedata.normalize('NFKC', unicode(mail['subject']))
                    .encode('ascii', 'ignore')) if x).lower()
            or 'untitled')
        while self.slug_used(rv):
            rv = increment_string(rv)
        return rv

    def walk(self):
        return self._known_ids.itervalues()

    def add_new_mail(self, f, fsid):
        mail = parse_mail(f, fsid)
        self._new_mail.append(mail)
        self._known_ids[mail['msgid']] = mail

    def add_thread_for(self, mail):
        self.threads.append({
            'title':        mail['subject'],
            'slug':         self.generate_slug(mail),
            'date':         mail['date'],
            'author':       mail['author'],
            'root':         mail,
            'reply_count':  0
        })

    def has_mail(self, msgid):
        return msgid in self._known_ids

    def get_mail(self, msgid):
        return self._known_ids.get(msgid)

    def find_parent(self, mail):
        # first check the reply to, some clients actually set that to
        # something useful :)
        if mail['in-reply-to']:
            referenced_mail = self.get_mail(mail['in-reply-to'])
            if referenced_mail is not None and referenced_mail is not mail:
                return referenced_mail

        # next check the references, pick the most recent one.
        last = last_date = None
        for msgid in mail['references']:
            referenced_mail = self.get_mail(msgid)
            if referenced_mail is None:
                continue
            other_date = parse_date(referenced_mail['date'])
            if last is None or last_date < other_date:
                last_date = other_date
                last = referenced_mail
        if last is not None and last is not mail:
            return last

        # oh boy, nothing matched, find the oldest matching subject
        # then.  That could take a while, we really check all mails...
        def _strip_subject(subject):
            if subject[:3].lower() in (u'aw:', u're:'):
                subject = subject[3:]
            return subject.strip().lower()
        subject = _strip_subject(mail['subject'])

        last = mail
        last_date = parse_date(mail['date'])
        for other_mail in self.walk():
            if _strip_subject(other_mail['subject']) == subject:
                other_date = parse_date(other_mail['date'])
                if last is None or other_date < last_date:
                    last = other_mail
                    last_date = other_date

        if last is not mail:
            return last

    def integrate_new_mail(self):
        while self._new_mail:
            mail = self._new_mail.pop()
            print "A", mail['msgid']
            parent = self.find_parent(mail)
            if parent is not None:
                parent['children'].append(mail)
            else:
                self.add_thread_for(mail)
            self.processed_mail.add(mail['fsid'])

        def _count_mails(children):
            rv = len(children)
            for child in children:
                rv += _count_mails(child['children'])
            return rv
        for thread in self.threads:
            thread['reply_count'] = _count_mails(thread['root']['children'])

    def save(self):
        for thread in self.threads:
            filename = os.path.join(THREAD_FOLDER, thread['slug'])
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError:
                pass
            with open(filename, 'w') as f:
                json.dump(thread, f, indent=2)

        with open(os.path.join(THREAD_FOLDER, 'threadlist'), 'w') as f:
            threads = sorted(self.threads, reverse=True,
                             key=lambda x: parse_date(x['date']))
            for idx, thread in enumerate(threads):
                thread = dict(thread)
                del thread['root']
                threads[idx] = thread
            json.dump(threads, f, indent=2)


def get_processed_tree():
    """Returns the tree of already processed mails (from
    the THREAD_FOLDER).
    """
    threads = []
    for thread in glob(THREAD_FOLDER + '/*/*/*/*'):
        if os.path.isfile(thread):
            with open(thread) as f:
                threads.append(json.load(f))

    return Tree(threads)


def parse_mail(f, fsid):
    """Parses an email and returns the information we care about"""
    msg = json.load(f)
    headers = Headers(msg['headers'])

    irt = None
    match = _msgid_re.search(headers.get('in-reply-to', ''))
    if match is not None:
        irt = unquote_msgid(match.group(1))
    references = [unquote_msgid(msgid) for msgid
                  in headers.get('references', '').split() if msgid]

    body = msg['body']
    if body is None:
        for part in msg['parts']:
            if part['encoding']['type'] == 'text/plain':
                body = part['body']
                break
        else:
            body = 'could not decode message'

    return {
        'fsid':         fsid,
        'msgid':        unquote_msgid(headers.get('message-id') or 'fakdeid-' + fsid),
        'in-reply-to':  irt,
        'references':   references,
        'author':       split_email(headers['from']),
        'date':         headers['Date'],
        'subject':      strip_subject_prefix(headers['subject'] or 'No Subject'),
        'text':         body,
        'children':     []
    }


def process_mails(tree):
    to_process = []

    # find the unprocessed mails
    for folder in glob('%s/%s/*/*/*/json' % (INCOMING_MAIL_FOLDER, LIST_NAME)):
        for fsid in os.listdir(folder):
            if fsid not in tree.processed_mail:
                filename = os.path.join(folder, fsid)
                if os.path.isfile(filename):
                    to_process.append((filename, fsid))

    # now parse all mails and append them to the tree as new mails
    for filename, fsid in to_process:
        with open(filename) as f:
            tree.add_new_mail(f, fsid)

    tree.integrate_new_mail()

    # and write the information to the file system
    tree.save()


def main():
    tree = get_processed_tree()
    rsync()
    process_mails(tree)


if __name__ == '__main__':
    main()
