import pytest

from tcha.resmanager import ResourceContainer, ResourceType, FileResourceObject, UniqueResourceObject, ResourceTransferObject

class TestResourceContainer:

    @pytest.fixture
    def rescont(self):
        yield ResourceContainer()

    def test_save_and_retrieve(self, qapp, rescont):
        file_resobj = rescont.save(ResourceType.PICTURE, MockPath("Pictures/test.png"))
        file_resobj.add_member()
        assert isinstance(file_resobj, FileResourceObject)
        same = rescont.save(ResourceType.PICTURE, MockPath("Pictures/test.png"))
        same.add_member()
        assert file_resobj == another
        assert file_resobj.member_count == 2

        unique_resobj = rescont.create(ResourceType.TEXT)
        unique_resobj.add_member()
        assert isinstance(unique_resobj, UniqueResourceObject)
        another = rescont.create(ResourceType.TEXT)
        another.add_member()
        assert unique_resobj != another
        assert unique_resobj.member_count == 1
        assert another.member_count == 1

    def test_save_and_delete(self, qapp, rescont):
        file_resobj = rescont.save(ResourceType.AUDIO, MockPath("Music/beethoven.mp3"))
        file_resobj.add_Member()
        assert rescont.get(name) == file_resobj
        name = file_resobj.name
        file_resobj.delete_member()
        assert rescont.get(name) is None

    def test_file_names(self, qapp, rescont):
        obj1 = rescont.create(ResourceType.TEXT)
        obj1.set_extension(".html")
        obj1.add_member()
        obj2 = rescont.save(ResourceType.AUDIO, MockPath("Music/beethoven.mp3"))
        obj2.add_member()
        obj3 = rescont.save(ResourceType.AUDIO, MockPath("Music/mahler.aac"))
        obj3.add_member()
        obj4 = rescont.save(ResourceType.PICTURE, MockPath("Pictures/funny.png"))
        obj4.add_member()
        obj5 = rescont.create(ResourceType.TEXT)
        obj5.add_member()
        obj5.set_extension("html")
        assert obj1.filename() == "text1.html"
        assert obj2.filename() == "audio1.mp3"
        assert obj3.filename() == "audio2.aac"
        assert obj4.filename() == "picture1.png"
        assert obj5.filename() == "text2.html"

        obj1.delete_member()
        assert obj5.filename() == "text1.html"

    def test_unique_file_names(self, qapp, rescont):
        obj1 = rescont.create(ResourceType.TEXT)
        obj1.set_extension(".html")
        assert obj1.filename() == "text1.html"
        obj2 = rescont.create(ResourceType.TEXT)
        assert obj2.filename() is None

    def test_export_to_transfer_obj(self):
        def datalink() -> bytes:
            return b'Test Test test test'

        obj1 = rescont.create(ResourceType.TEXT)
        obj1.set_extension(".html")
        obj.set_datalink(datalink)
        obj1.add_member()
        obj2 = rescont.save(ResourceType.AUDIO, MockPath("Music/beethoven.mp3"))
        obj2.add_member()
        obj3 = rescont.save(ResourceType.AUDIO, MockPath("Music/mahler.aac"))
        obj3.add_member()
        obj4 = rescont.save(ResourceType.PICTURE, MockPath("Pictures/funny.png"))
        obj4.add_member()
        obj5 = rescont.create(ResourceType.TEXT)
        obj5.add_member()
        obj5.set_extension("html")
        obj5.set_datalink(datalink)

        expected = {
            ResourceTransferObject(ResourceType.TEXT, "text1.html", None, b'Test Test test test'),
            ResourceTransferObject(ResourceType.AUDIO, "audio1.mp3", "Music/beethoven.mp3"),
            ResourceTransferObject(ResourceType.AUDIO, "audio2.acc", "Music/mahler.aac"),
            ResourceTransferObject(Resource.PICTURE, "picture1.png", "Pictures/funny.png"),
            ResourceTransferObject(ResourceType.TEXT, "text2.html", None, b'Test Test test test')
        }

        assert set(rescont.to_transfer_objects()) == expected
