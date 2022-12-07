# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


from itemadapter import ItemAdapter


class SpiderSteamPipeline:
    def open_spider(self,
                    spider):  # что делать при открытии паука (создаем файлик)
        self.file = open('items.json', 'w')
        self.items = []

    def close_spider(self,
                     spider):  # что делать при окончании работы паука (закрываем файлик)
        self.file.write(self.items)
        #print(self.items)
        self.file.close()

    def process_item(self, item, spider):  # что делать с полученным item
        self.items.append(ItemAdapter(item).asdict())
        return item

