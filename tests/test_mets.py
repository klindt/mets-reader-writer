import filecmp
from lxml import etree
import os
import pytest
from unittest import TestCase
import uuid

import metsrw

class TestMETSDocument(TestCase):
    """ Test METSDocument class. """

    def test_fromfile(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)
        mw = metsrw.METSDocument.fromfile('fixtures/complete_mets.xml')
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_fromstring(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)
        with open('fixtures/complete_mets.xml', 'rb') as f:
            metsstring = f.read()
        mw = metsrw.METSDocument.fromstring(metsstring)
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_fromtree(self):
        root = etree.parse('fixtures/complete_mets.xml')
        mw = metsrw.METSDocument.fromtree(root)
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_parse(self):
        """
        It should set the correct createdate.
        It should create FSEntrys for every file and directory.
        It should associate amdSec and dmdSec with the FSEntry.
        It should associated derived files.
        """
        mw = metsrw.METSDocument()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)
        mw.tree = root
        mw._parse_tree()
        assert mw.createdate == '2014-07-23T21:48:33'
        assert len(mw.all_files()) == 14
        assert mw.get_file(type='Directory', label='csv-48accdf3-e425-4874-aad3-67ade019a214') is not None
        parent = mw.get_file(type='Directory', label='objects')
        assert parent is not None
        f = mw.get_file(type='Item', label='Landing_zone.jpg')
        assert f is not None
        assert f.path == 'objects/Landing_zone.jpg'
        assert f.use == 'original'
        assert f.parent == parent
        assert f.children == []
        assert f.file_uuid == 'ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2'
        assert f.derived_from is None
        assert f.admids == ['amdSec_1']
        assert f.dmdids == ['dmdSec_1']
        assert f.file_id() == 'file-ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2'
        assert f.group_id() == 'Group-ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2'
        f = mw.get_file(type='Item', label='Landing_zone-fc33fc0e-40ef-4ad9-ba52-860368e8ce5a.tif')
        assert f is not None
        assert f.path == 'objects/Landing_zone-fc33fc0e-40ef-4ad9-ba52-860368e8ce5a.tif'
        assert f.use == 'preservation'
        assert f.parent == parent
        assert f.children == []
        assert f.file_uuid == 'e284d015-cfb0-45dd-961d-512bf0f47cf6'
        assert f.derived_from == mw.get_file(type='Item', label='Landing_zone.jpg')
        assert f.admids == ['amdSec_2']
        assert f.dmdids == []
        assert f.file_id() == 'file-e284d015-cfb0-45dd-961d-512bf0f47cf6'
        assert f.group_id() == 'Group-ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2'
        assert mw.get_file(type='Directory', label='metadata') is not None
        assert mw.get_file(type='Directory', label='transfers') is not None
        assert mw.get_file(type='Directory', label='csv-55599568-90bd-46ac-b1be-d1a538793cae') is not None
        assert mw.get_file(type='Directory', label='submissionDocumentation') is not None
        assert mw.get_file(type='Directory', label='transfer-csv-55599568-90bd-46ac-b1be-d1a538793cae') is not None

    def test_parse_tree_createdate_too_new(self):
        mw = metsrw.METSDocument()
        root = etree.parse('fixtures/createdate_too_new.xml')
        mw.tree = root
        with pytest.raises(metsrw.ParseError):
            mw._parse_tree()

    def test_parse_tree_no_createdate(self):
        mw = metsrw.METSDocument()
        mets_string = b"""<?xml version='1.0' encoding='ASCII'?>
<mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
  <metsHdr/><structMap TYPE="physical"></structMap>
</mets>
"""
        root = etree.fromstring(mets_string)
        mw.tree = root
        mw._parse_tree()
        assert mw.createdate is None

    def test_parse_no_groupid(self):
        """ It should handle files with no GROUPID. """
        mw = metsrw.METSDocument().fromfile('fixtures/mets_without_groupid_in_file.xml')
        assert mw.get_file(file_uuid='db653873-d0ab-4bc1-9edb-2b6d2d84ab5a') is not None

    def test_write(self):
        mw = metsrw.METSDocument()
        # mock serialize
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser).getroot()
        mw.serialize = lambda fully_qualified: root
        mw.write('test_write.xml', pretty_print=True)
        assert filecmp.cmp('fixtures/complete_mets.xml', 'test_write.xml', shallow=False)
        os.remove('test_write.xml')

    def test_mets_root(self):
        mw = metsrw.METSDocument()
        root = mw._document_root()
        location = "http://www.loc.gov/METS/ " + \
            "http://www.loc.gov/standards/mets/version18/mets.xsd"
        assert root.tag == '{http://www.loc.gov/METS/}mets'
        assert root.attrib[metsrw.lxmlns('xsi') + 'schemaLocation'] == location
        nsmap = {
            'mets': "http://www.loc.gov/METS/",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance",
            'xlink': "http://www.w3.org/1999/xlink",
        }
        assert root.nsmap == nsmap

    def test_mets_header(self):
        mw = metsrw.METSDocument()
        date = '2014-07-16T22:52:02.480108'
        header = mw._mets_header(date)
        assert header.tag == '{http://www.loc.gov/METS/}metsHdr'
        assert header.attrib['CREATEDATE'] == date

    def test_mets_header_lastmoddate(self):
        mw = metsrw.METSDocument()
        date = '2014-07-16T22:52:02.480108'
        new_date = '3014-07-16T22:52:02.480108'
        mw.createdate = date
        header = mw._mets_header(new_date)
        assert header.tag == '{http://www.loc.gov/METS/}metsHdr'
        assert header.attrib['CREATEDATE'] == date
        assert header.attrib['LASTMODDATE'] == new_date
        assert header.attrib['CREATEDATE'] < header.attrib['LASTMODDATE']


class TestWholeMETS(TestCase):
    """ Test integration between classes. """

    def test_files(self):
        # Test collects several children deep
        f3 = metsrw.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()))
        d2 = metsrw.FSEntry('dir2', type='Directory', children=[f3])
        f2 = metsrw.FSEntry('level2.txt', file_uuid=str(uuid.uuid4()))
        d1 = metsrw.FSEntry('dir1', type='Directory', children=[d2, f2])
        f1 = metsrw.FSEntry('level1.txt', file_uuid=str(uuid.uuid4()))
        d = metsrw.FSEntry('root', type='Directory', children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        files = mw.all_files()
        assert files
        assert len(files) == 6
        assert d in files
        assert f1 in files
        assert d1 in files
        assert f2 in files
        assert d2 in files
        assert f3 in files
        f4_uuid = str(uuid.uuid4())
        f4 = metsrw.FSEntry('file4.txt', file_uuid=f4_uuid)
        mw.append_file(f4)
        files = mw.all_files()
        assert len(files) == 7
        assert f4 in files

    def test_add_file_to_child(self):
        # Test collects several children deep
        f2 = metsrw.FSEntry('level2.txt', file_uuid=str(uuid.uuid4()))
        d1 = metsrw.FSEntry('dir1', type='Directory', children=[f2])
        f1 = metsrw.FSEntry('level1.txt', file_uuid=str(uuid.uuid4()))
        d = metsrw.FSEntry('root', type='Directory', children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        files = mw.all_files()
        assert files
        assert len(files) == 4
        assert d in files
        assert f1 in files
        assert d1 in files
        assert f2 in files

        f3 = metsrw.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()))
        d1.add_child(f3)
        files = mw.all_files()
        assert len(files) == 5
        assert f3 in files

    def test_get_file(self):
        # Setup
        f3_uuid = str(uuid.uuid4())
        f3 = metsrw.FSEntry('dir1/dir2/level3.txt', file_uuid=f3_uuid)
        d2 = metsrw.FSEntry('dir1/dir2', type='Directory', children=[f3])
        f2_uuid = str(uuid.uuid4())
        f2 = metsrw.FSEntry('dir1/level2.txt', file_uuid=f2_uuid)
        d1 = metsrw.FSEntry('dir1', type='Directory', children=[d2, f2])
        f1_uuid = str(uuid.uuid4())
        f1 = metsrw.FSEntry('level1.txt', file_uuid=f1_uuid)
        d = metsrw.FSEntry('root', type='Directory', children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        # Test
        # By UUID
        assert mw.get_file(file_uuid=f3_uuid) == f3
        assert mw.get_file(file_uuid=f2_uuid) == f2
        assert mw.get_file(file_uuid=f1_uuid) == f1
        assert mw.get_file(file_uuid='does not exist') is None
        # By path
        assert mw.get_file(path='dir1/dir2/level3.txt') == f3
        assert mw.get_file(path='dir1/dir2') == d2
        assert mw.get_file(path='dir1/level2.txt') == f2
        assert mw.get_file(path='dir1') == d1
        assert mw.get_file(path='level1.txt') == f1
        assert mw.get_file(path='does not exist') is None
        # By label
        assert mw.get_file(label='level3.txt') == f3
        assert mw.get_file(label='dir2') == d2
        assert mw.get_file(label='level2.txt') == f2
        assert mw.get_file(label='dir1') == d1
        assert mw.get_file(label='level1.txt') == f1
        assert mw.get_file(label='does not exist') is None
        # By multiple
        assert mw.get_file(label='level3.txt', path='dir1/dir2/level3.txt') == f3
        assert mw.get_file(label='dir2', type='Directory') == d2
        assert mw.get_file(label='level2.txt', type='Item') == f2
        assert mw.get_file(file_uuid=None, type='Item') is None
        # Updates list
        f4_uuid = str(uuid.uuid4())
        f4 = metsrw.FSEntry('file4.txt', file_uuid=f4_uuid)
        mw.append_file(f4)
        assert mw.get_file(file_uuid=f4_uuid) == f4
        assert mw.get_file(path='file4.txt') == f4

    def test_remove_file(self):
        """ It should """
        # Setup
        f3_uuid = str(uuid.uuid4())
        f3 = metsrw.FSEntry('dir1/dir2/level3.txt', file_uuid=f3_uuid)
        d2 = metsrw.FSEntry('dir1/dir2', type='Directory', children=[f3])
        f2_uuid = str(uuid.uuid4())
        f2 = metsrw.FSEntry('dir1/level2.txt', file_uuid=f2_uuid)
        d1 = metsrw.FSEntry('dir1', type='Directory', children=[d2, f2])
        f1_uuid = str(uuid.uuid4())
        f1 = metsrw.FSEntry('level1.txt', file_uuid=f1_uuid)
        d = metsrw.FSEntry('root', type='Directory', children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        assert len(mw.all_files()) == 6
        # Test remove file
        mw.remove_entry(f3)
        assert len(mw.all_files()) == 5
        assert mw.get_file(file_uuid=f3_uuid) is None
        assert f3 not in d2.children
        assert f3 not in mw.all_files()
        # Test remove dir
        mw.remove_entry(d1)
        assert len(mw.all_files()) == 2
        assert mw.get_file(path='dir1') is None
        assert d1 not in d.children
        assert d1 not in mw.all_files()
        assert f2 not in mw.all_files()
        assert d2 not in mw.all_files()
        assert f1 in d.children
        # Test remove root element
        mw.remove_entry(d)
        assert len(mw.all_files()) == 0

    def test_collect_mdsec_elements(self):
        f1 = metsrw.FSEntry('file1.txt', file_uuid=str(uuid.uuid4()))
        f1.amdsecs.append(metsrw.AMDSec())
        f1.dmdsecs.append(metsrw.SubSection('dmdSec', None))
        f2 = metsrw.FSEntry('file2.txt', file_uuid=str(uuid.uuid4()))
        f2.dmdsecs.append(metsrw.SubSection('dmdSec', None))
        mw = metsrw.METSDocument()
        elements = mw._collect_mdsec_elements([f1, f2])
        # Check ordering - dmdSec before amdSec
        assert isinstance(elements, list)
        assert len(elements) == 3
        assert isinstance(elements[0], metsrw.SubSection)
        assert elements[0].subsection == 'dmdSec'
        assert isinstance(elements[1], metsrw.SubSection)
        assert elements[1].subsection == 'dmdSec'
        assert isinstance(elements[2], metsrw.AMDSec)

    def test_filesec(self):
        o = metsrw.FSEntry('objects/file1.txt', file_uuid=str(uuid.uuid4()))
        p = metsrw.FSEntry('objects/file1-preservation.txt', use='preservaton', file_uuid=str(uuid.uuid4()))
        o2 = metsrw.FSEntry('objects/file2.txt', file_uuid=str(uuid.uuid4()))
        mw = metsrw.METSDocument()
        element = mw._filesec([o, p, o2])
        assert isinstance(element, etree._Element)
        assert element.tag == '{http://www.loc.gov/METS/}fileSec'
        assert len(element) == 2  # 2 groups
        assert element[0].tag == '{http://www.loc.gov/METS/}fileGrp'
        assert element[0].get('USE') == 'original'
        assert element[1].tag == '{http://www.loc.gov/METS/}fileGrp'
        assert element[1].get('USE') == 'preservaton'
        # TODO test file & FLocat

    def test_structmap(self):
        """
        It should create a structMap tag.
        It should have a div tag for the directory.
        It should have div tags for the children beneath the directory.
        It should not have div tags for deleted files (without label).
        """
        children = [
            metsrw.FSEntry('objects/file1.txt', file_uuid=str(uuid.uuid4())),
            metsrw.FSEntry('objects/file2.txt', file_uuid=str(uuid.uuid4())),
        ]
        parent = metsrw.FSEntry('objects', type='Directory', children=children)
        deleted_f = metsrw.FSEntry(use='deletion', file_uuid=str(uuid.uuid4()))

        writer = metsrw.METSDocument()
        writer.append_file(parent)
        writer.append_file(deleted_f)
        sm = writer._structmap()

        assert sm.tag == '{http://www.loc.gov/METS/}structMap'
        assert sm.attrib['TYPE'] == 'physical'
        assert sm.attrib['ID'] == 'structMap_1'
        assert sm.attrib['LABEL'] == 'Archivematica default'
        assert len(sm.attrib) == 3
        assert len(sm) == 1
        parent = sm[0]
        assert parent.tag == '{http://www.loc.gov/METS/}div'
        assert parent.attrib['LABEL'] == 'objects'
        assert parent.attrib['TYPE'] == 'Directory'
        assert len(parent.attrib) == 2
        assert len(parent) == 2
        assert parent[0].attrib['LABEL'] == 'file1.txt'
        assert parent[0].attrib['TYPE'] == 'Item'
        assert len(parent[0].attrib) == 2
        assert parent[0].find('{http://www.loc.gov/METS/}fptr') is not None
        assert parent[1].attrib['LABEL'] == 'file2.txt'
        assert parent[1].attrib['TYPE'] == 'Item'
        assert len(parent[1].attrib) == 2
        assert parent[1].find('{http://www.loc.gov/METS/}fptr') is not None

    def test_full_mets(self):
        mw = metsrw.METSDocument()
        file1 = metsrw.FSEntry('objects/object1.ext', file_uuid=str(uuid.uuid4()))
        file2 = metsrw.FSEntry('objects/object2.ext', file_uuid=str(uuid.uuid4()))
        file1p = metsrw.FSEntry('objects/object1-preservation.ext', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file1)
        file2p = metsrw.FSEntry('objects/object2-preservation.ext', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file2)
        children = [file1, file2, file1p, file2p]
        objects = metsrw.FSEntry('objects', type='Directory', children=children)
        children = [
            metsrw.FSEntry('transfers', type='Directory', children=[]),
            metsrw.FSEntry('metadata/metadata.csv', use='metadata', file_uuid=str(uuid.uuid4())),
        ]
        metadata = metsrw.FSEntry('metadata', type='Directory', children=children)
        children = [
            metsrw.FSEntry('submissionDocumentation/METS.xml', use='submissionDocumentation', file_uuid=str(uuid.uuid4())),
        ]
        sub_doc = metsrw.FSEntry('submissionDocumentation', type='Directory', children=children)
        children = [objects, metadata, sub_doc]
        sip = metsrw.FSEntry('sipname-uuid', type='Directory', children=children)
        sip.add_dublin_core('<dublincore>sip metadata</dublincore>')
        file1.add_premis_object('<premis>object</premis>')
        file1.add_premis_event('<premis>event</premis>')
        file1.add_premis_agent('<premis>agent</premis>')
        rights = file1.add_premis_rights('<premis>rights</premis>')
        rights.replace_with(file1.add_premis_rights('<premis>newer rights</premis>'))
        dc = file1.add_dublin_core('<dublincore>metadata</dublincore>')
        dc.replace_with(file1.add_dublin_core('<dublincore>newer metadata</dublincore>'))

        mw.append_file(sip)
        mw.write('full_metsrw.xml', fully_qualified=True, pretty_print=True)

        os.remove('full_metsrw.xml')
