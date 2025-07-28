import random
from PyQt6.QtCore import QDateTime
from tcha.resmanager import ResourceType, ResourceContainer
from tcha.tablemodel import TableModel
from tcha.elements import textelement, audioelement, pictureelement
from tcha.dbmodels import CourseModel, ScheduleModel, StudentModel

TEXT1 = """
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:14pt;">Hier ist ein kleiner </span><span style=" font-size:18pt; font-weight:600;">Beispieltext</span><span style=" font-size:14pt;">, der </span><span style=" font-size:14pt; font-weight:600; color:#aa0000;">abgespeichert </span><span style=" font-size:14pt;">werden soll!</span></p></body></html>
"""
TEXT2 = """
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Sum the <span style=" font-weight:600;">digits of the first operand</span>; any <span style=" text-decoration: underline; color:#55aa00;">9s</span> (or sets of digits that add to 9) can be counted as 0.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:16pt; font-style:italic;">If the resulting sum has two or more digits</span>, sum those digits as in <span style=" color:#55aaff;">step one</span>; repeat this step until the resulting sum has only one digit.</p></body></html>
"""

TEXT3 = """
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;">
<p style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="Comparison"></a><span style=" font-size:large; font-weight:600;">C</span><span style=" font-size:large; font-weight:600;">omparison</span></p>
<p style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">If <span style=" font-weight:600; text-decoration: underline; color:#ff5500;">two integers</span><span style=" text-decoration: underline; color:#ff5500;"> </span>are equal, then all their residues are equal. Conversely, if all residues are equal, then the two integers are equal, or their differences is a multiple of <span style=" font-style:italic;">M</span>. <span style=" font-size:12pt; font-weight:600;">It follows that </span><span style=" font-size:12pt; font-weight:600; color:#aa00ff;">testing equality</span><span style=" font-size:12pt; font-weight:600;"> is easy. </span></p></body></html>
"""



def test_model(rescont: ResourceContainer) -> TableModel:
    table = TableModel.new(2, 2)

    texts = (TEXT1, TEXT2, TEXT3)

    image_files = [
        "D:/Bilder/312WEQ3JPPL.jpg",
        "D:/Bilder/Bilder Interuni The Best/Image_5e22853.jpg",
        "D:/Bilder/Bilder Interuni The Best/Image_16af2af.jpg"
    ]  # Adjust path as needed
    audio_files = [
        "D:/Musik/AAAMYYY - TAKES TIME.mp3",
        "D:/Musik/YUKI - Joy.mp3",
        "D:/Musik/TOMOO - Ginger.mp3"
    ] # Adjust path as needed
    

# Cell 0,0 - Text + Audio
    text_obj = rescont.create(ResourceType.TEXT)
    text_obj.add_member()
    text_model = textelement.TextModel(text_obj)
    text_model.setHtml(random.choice(texts))
    
    audio_obj = rescont.save(ResourceType.AUDIO, random.choice(audio_files))
    audio_obj.add_member()
    audio_model = audioelement.AudioModel(audio_obj)
    
    cell_00 = table.data(table.index(0, 0))
    cell_00.add_model(text_model)
    cell_00.add_model(audio_model)

    # Cell 0,1 - Picture + Text
    pic_obj = rescont.save(ResourceType.IMAGE, random.choice(image_files))
    pic_obj.add_member()
    pic_model = pictureelement.PictureModel(pic_obj, 100, 100)
    
    text_obj2 = rescont.create(ResourceType.TEXT)
    text_obj2.add_member()
    text_model2 = textelement.TextModel(text_obj2)
    text_model2.setHtml(random.choice(texts))
    
    cell_01 = table.data(table.index(0, 1))
    cell_01.add_model(pic_model)
    cell_01.add_model(text_model2)

    # Cell 1,0 - Picture + Audio + Text
    pic_obj2 = rescont.save(ResourceType.IMAGE, random.choice(image_files))
    pic_obj2.add_member()
    pic_model2 = pictureelement.PictureModel(pic_obj2, 100, 100)
    
    audio_obj2 = rescont.save(ResourceType.AUDIO, random.choice(audio_files))
    audio_obj2.add_member()
    audio_model2 = audioelement.AudioModel(audio_obj2)
    
    text_obj3 = rescont.create(ResourceType.TEXT)
    text_obj3.add_member()
    text_model3 = textelement.TextModel(text_obj3)
    text_model3.setHtml(random.choice(texts))
    
    cell_10 = table.data(table.index(1, 0))
    cell_10.add_model(pic_model2)
    cell_10.add_model(audio_model2)
    cell_10.add_model(text_model3)

    # Cell 1,1 - Two Text Elements with different formatting
    text_obj4 = rescont.create(ResourceType.TEXT)
    text_obj4.add_member()
    text_model4 = textelement.TextModel(text_obj4)
    text_model4.setHtml(random.choice(texts))
    
    text_obj5 = rescont.create(ResourceType.TEXT)
    text_obj5.add_member()
    text_model5 = textelement.TextModel(text_obj5)
    text_model5.setHtml(random.choice(texts))
    
    cell_11 = table.data(table.index(1, 1))
    cell_11.add_model(text_model4)
    cell_11.add_model(text_model5)

    return table

def test_lesson_models(db) -> CourseModel | ScheduleModel | StudentModel:
    cmodel = CourseModel(db)
    cmodel.add_course("A1 Business (Oct 2023)", 90)
    cmodel.add_course("Feng", 45)
    cmodel.add_course("A1 Intensiv Aug 2024", 150)
    cmodel.add_course("Aoki", 60)

    smodel = ScheduleModel(db)
    smodel.add_schedule(1, QDateTime(2025, 6, 15, 14, 30, 0), "D:/Dokumente/thislesson.lesson")
    smodel.add_schedule(2, QDateTime(2020, 1, 6, 10, 15, 0), "D:/Dokumente/thislesson.lesson") 
    smodel.add_schedule(3, QDateTime(2022, 8, 31, 12, 0, 0), "D:/Dokumente/thislesson.lesson")
    smodel.add_schedule(4, QDateTime(2019, 12, 20, 11, 20, 0), "D:/Dokumente/thislesson.lesson")

    tmodel = StudentModel(db)
    tmodel.add_student("Yuta Katsumata", 1)
    tmodel.add_student("Yukiko Wada", 1)
    tmodel.add_student("Hiroki Shinoda", 1)
    tmodel.add_student("Hongyu Feng", 2)
    tmodel.add_student("Chika Okura", 3)
    tmodel.add_student("Akihisa Yamada", 3)
    tmodel.add_student("Ayumi Oshima", 3)
    tmodel.add_student("Aya Shinozaki", 3)
    tmodel.add_student("Hiromi Fujisawa", 3)
    tmodel.add_student("Amane Tomita", 3)
    tmodel.add_student("Ayako Kimura", 3)
    tmodel.add_student("Hisayuki Aoki", 4)

    return cmodel, smodel, tmodel