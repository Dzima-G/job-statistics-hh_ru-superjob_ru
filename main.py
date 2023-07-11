import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if not salary_from:
        salary_from = None
    if not salary_to:
        salary_to = None
    if salary_from and salary_to:
        income_average = (int(salary_from) + int(salary_to)) / 2
        return income_average
    if salary_from:
        income_average = int(salary_from) * 1.2
        return income_average
    if salary_to:
        income_average = int(salary_to) * 0.8
        return income_average
    return None


def predict_rub_salary_hh(vacancy):
    average_salaries = []
    city = 1
    found = 0
    page = 0
    while True:
        page += 1
        payload = {"text": {vacancy}, "area": city, "per_page": "50", "page": {page}}
        response = requests.get("https://api.hh.ru/vacancies", params=payload)
        vacancy_data = response.json()
        if "items" not in vacancy_data:
            break
        if page == 1:
            found = vacancy_data["found"]
        for item_vacancy in (vacancy_data["items"]):
            if item_vacancy["salary"] is not None and item_vacancy["salary"]["currency"] in "RUR":
                average_salaries.append(
                    predict_salary(item_vacancy["salary"]["from"], item_vacancy["salary"]["to"])
                )
    return average_salaries, found


def predict_rub_salary_sj(vacancy):
    headers_sj = {"X-Api-App-Id": sj_secret_key}
    city = 4
    industries_sections = 48
    page = 0
    average_salaries = []
    while True:
        payload = {"keyword": vacancy, "town": city, "catalogues": industries_sections, "count": "50", "page": page}
        response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers_sj, params=payload)
        response.raise_for_status()
        vacancy_data = response.json()
        if not len(vacancy_data['objects']):
            break
        for item_vacancy in vacancy_data['objects']:
            if item_vacancy['currency'] == "rub":
                average_salaries.append(
                    predict_salary(item_vacancy['payment_from'], item_vacancy['payment_to'])
                )
        page += 1
    return average_salaries


def get_output_table(data, title):
    vacancies_information = list(data)
    format_table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for vacancy in vacancies_information:
        format_table.append([vacancy,
                             data[vacancy]["vacancies_found"],
                             data[vacancy]["vacancies_processed"],
                             data[vacancy]["average_salary"]
                             ])
    table = AsciiTable(format_table)
    table.title = title
    return table.table


def get_average_salary(response_vacancy):
    averages_salaries, number_vacancies = response_vacancies
    if not number_vacancies:
        salary_statistics = {"vacancies_found": 0,
                             "vacancies_processed": 0,
                             "average_salary": 0
                             }
        return salary_statistics
    averages_salaries = [x for x in averages_salaries if x]
    if len(averages_salaries):
        average_salary = int(sum(averages_salaries) / len(averages_salaries))
    else:
        average_salary = int(sum(averages_salaries))
    salary_statistics = {"vacancies_found": number_vacancies,
                         "vacancies_processed": len(averages_salaries),
                         "average_salary": average_salary,
                         }
    return salary_statistics


if __name__ == "__main__":
    load_dotenv()
    sj_secret_key = os.environ['SUPER_JOB_SECRET_KEY']
    vacancies = ["Программист Python", "Программист Java", "Программист JavaScript", "Программист Ruby",
                 "Программист PHP", "Программист C++", "Программист C#", "Программист C", "Программист Go",
                 "Программист Swift"]
    table_output_vacancies = dict.fromkeys(vacancies)

    for vacancy in vacancies:
        try:
            response_vacancies = predict_rub_salary_hh(vacancy)
        except requests.exceptions.HTTPError:
            print('Ошибка! Некорректная ссылка')

        vacancy_statistics = get_average_salary(response_vacancies)
        print(vacancy_statistics)
        table_output_vacancies[vacancy] = vacancy_statistics
    print(get_output_table(table_output_vacancies, 'HeadHunter Moscow'))

    for vacancy in vacancies:
        try:
            response_vacancies = predict_rub_salary_sj(vacancy)
        except requests.exceptions.HTTPError:
            print('Ошибка! Некорректная ссылка')

        response_vacancies = (response_vacancies, len(response_vacancies))
        vacancy_statistics = get_average_salary(response_vacancies)
        table_output_vacancies[vacancy] = vacancy_statistics
    print(get_output_table(table_output_vacancies, 'SuperJob Moscow'))
