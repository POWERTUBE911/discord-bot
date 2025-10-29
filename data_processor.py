import json

def calculate_level(points, rewards_levels):
    """تحسب مستوى العصابة بناءً على النقاط وقائمة المستويات."""
    level = 0
    for reward in rewards_levels:
        if points >= reward['points']:
            level = reward['level']
        else:
            break
    return level

def process_gang_data(file_path):
    """تقوم بتحميل البيانات وحساب المستوى لكل عصابة."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rewards_levels = data['rewards_levels']
    
    # تحديث النقاط والمستويات لغرض العرض التجريبي
    # (هذه البيانات الافتراضية، في البوت الحقيقي سيتم جلبها من قاعدة بيانات حية)
    data['gangs'][0]['points'] = 150 # البلود
    data['gangs'][1]['points'] = 30  # المافيا
    data['gangs'][2]['points'] = 265 # القروف ستريت
    
    for gang in data['gangs']:
        gang['level'] = calculate_level(gang['points'], rewards_levels)
        
    return data['gangs']

if __name__ == '__main__':
    # سيتم استخدام هذه الدالة لاحقًا في ملف البوت
    pass
