import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if salary_from is None or salary_from <= 0:
        salary_from = None
    if salary_to is None or salary_to <= 0:
        salary_to = None
    if salary_from is not None and salary_to is not None:
        income_average = (int(salary_from) + int(salary_to)) / 2
        return income_average
    if salary_from is not None:
        income_average = int(salary_from) * 1.2
        return income_average
    if salary_to is not None:
        income_average = int(salary_to) * 0.8
        return income_average
    return None


def predict_rub_salary_hh(vacancy):
    profession = []
    found = 0
    page = 0
    while True:
        page += 1
        payload = {"text": {vacancy}, "area": "1", "per_page": "50", "page": {page}}
        response = requests.get("https://api.hh.ru/vacancies", params=payload)
        data = response.json()
        print(data)
        if "items" not in data:
            break
        if page == 1:
            found = data["found"]
        for item_vacancy in (data["items"]):
            if item_vacancy["salary"] is not None and item_vacancy["salary"]["currency"] in "RUR":
                predict_salary(item_vacancy["salary"]["from"], item_vacancy["salary"]["to"])
                profession.append([
                    f"{item_vacancy['name']}",
                    f"{item_vacancy['area']['name']}",
                    predict_salary(item_vacancy["salary"]["from"], item_vacancy["salary"]["to"])
                ])
    return profession, found


def predict_rub_salary_sj(vacancy):
    headers_sj = {"X-Api-App-Id": sj_secret_key}
    page = 0
    profession = []
    while True:
        payload = {"keyword": vacancy, "town": "4", "catalogues": "48", "count": "50", "page": page}
        response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers_sj, params=payload)
        response.raise_for_status()
        data = response.json()
        if len(data['objects']) == 0:
            break
        for item_vacancy in data['objects']:
            if item_vacancy['currency'] == "rub":
                profession.append(
                    [f"{item_vacancy['profession']}", f"{item_vacancy['town']['title']}",
                     predict_salary(item_vacancy['payment_from'], item_vacancy['payment_to'])])
        page += 1
    return profession, len(profession)


def get_output_table(data, title):
    keys = list(data)
    format_table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for item in keys:
        format_table.append([item,
                             data[item]["vacancies_found"],
                             data[item]["vacancies_processed"],
                             data[item]["average_salary"]
                             ])
    table = AsciiTable(format_table)
    table.title = title
    return table.table


def get_average_salary(list_vacancies, source):
    data = dict.fromkeys(list_vacancies)
    for vacancy in list_vacancies:
        salary_statistics = {"vacancies_found": None, "vacancies_processed": None, "average_salary": None}
        if source == "sj":
            income_response = predict_rub_salary_sj(vacancy)
        else:
            income_response = predict_rub_salary_hh(vacancy)
        if income_response[1] == 0:
            salary_statistics["vacancies_found"] = 0
            salary_statistics["vacancies_processed"] = 0
            salary_statistics["average_salary"] = 0
            data[vacancy] = salary_statistics
            continue
        salary_statistics["vacancies_found"] = income_response[1]
        processed_data = [x[2] for x in income_response[0] if x[2] is not None]
        salary_statistics["vacancies_processed"] = len(processed_data)
        salary_statistics["average_salary"] = int(sum(processed_data) / len(processed_data))
        data[vacancy] = salary_statistics
    return data


if __name__ == "__main__":
    load_dotenv()
    sj_secret_key = os.environ['SUPER_JOB_SECRET_KEY']
    vacancies = ["Программист Python", "Программист Java", "Программист JavaScript", "Программист Ruby",
                 "Программист PHP", "Программист C++", "Программист C#", "Программист C", "Программист Go",
                 "Программист Swift"]

    try:
        print(get_output_table(get_average_salary(vacancies, "hh"), 'HeadHunter Moscow'))
    except requests.exceptions.HTTPError:
        print('Ошибка! Некорректная ссылка')

    try:
        print(get_output_table(get_average_salary(vacancies, "sj"), 'SuperJob Moscow'))
    except requests.exceptions.HTTPError:
        print('Ошибка! Некорректная ссылка')
