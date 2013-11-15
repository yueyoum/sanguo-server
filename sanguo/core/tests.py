from core.drives import document_char, mongodb_client, mongodb_client_db

class TestDocument(object):
    def setUp(self):
        self.data = {
                'a': 12,
                'b': 'hello',
                'c': [1,2,3]
                }
        document_char.set(1, **self.data)

    def tearDown(self):
        mongodb_client.drop_database(mongodb_client_db)

    def test_get(self):
        data = document_char.get(1, _id=0, a=1)
        assert len(data) == 1
        assert data['a'] == self.data['a']

        data = document_char.get(1)
        for k, v in data.items():
            if k == '_id':
                assert v == 1
                continue
            assert v == self.data[k]

        assert document_char.get(2) is None


    def test_list_field(self):
        document_char.add_to_list(1, 'c', 5)

        data = document_char.get(1)
        assert len(data) == 4
        assert len(data['c']) == 4
        assert 5 in data['c']

        document_char.add_to_list(1, 'c', [6, 7, 8])

        data = document_char.get(1)
        assert len(data) == 4
        assert len(data['c']) == 7
        assert 6 in data['c']
        assert 7 in data['c']
        assert 8 in data['c']


        document_char.remove_from_list(1, 'c', 6)

        data = document_char.get(1)
        assert len(data) == 4
        assert len(data['c']) == 6
        assert 6 not in data['c']

        document_char.remove_from_list(1, 'c', [7, 8])

        data = document_char.get(1)
        assert len(data) == 4
        assert len(data['c']) == 4
        assert 7 not in data['c']
        assert 8 not in data['c']


    def test_remove(self):
        document_char.set(2, **self.data)
        data = document_char.get(2)
        assert len(data) == 4

        document_char.remove(2)
        assert document_char.get(2) is None





