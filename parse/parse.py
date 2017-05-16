import json
import requests

RULE_KEY_NAME = "key_name"
RULE_CONTENT = "content"
RULE_SUBRULE = "subsections"

def ruleTemplate(content, options, conditionString, name, description, parentIndex=None):
	if options:
		optionsWithIndex = []
		for i in xrange(len(options)):
			if parentIndex:
				optionsWithIndex.append("({parentIndex}.{currentIndex}) {title}".format(
					parentIndex=parentIndex,
					currentIndex=i + 1,
					title=options[i]
				))
			else:
				optionsWithIndex.append("({currentIndex}) {title}".format(
					currentIndex=i + 1,
					title=options[i]
				))

		action = [
			"sendMessageToVisitor",
			"Customer Service",
			content,
			"/".join(optionsWithIndex)
		]
	else:
		action = [
			"sendMessageToVisitor",
			"Customer Service",
			content
		]

	return {
		"definition": {
			"actions": [
				action
			],
			"event": "chat_message",
			"condition": [
				"or",
				[
					"icontains",
					"@message",
					conditionString
				]
			],
		},
		"enabled": True,
		"description": description,
		"name": name
	}


def parseRule(rule, parentRule, parentRuleIndex):
	content = rule[RULE_CONTENT]
	options = [subrule[RULE_KEY_NAME] for subrule in rule[RULE_SUBRULE]] if RULE_SUBRULE in rule else []
	conditionString = rule[RULE_KEY_NAME]
	name = rule[RULE_KEY_NAME]
	description = rule[RULE_CONTENT]
	parsedRules = []
	parsedRules.append(ruleTemplate(content, options, conditionString, name, description, parentIndex=parentRuleIndex))
	for i in xrange(len(rule.get(RULE_SUBRULE, []))):
		subRule = rule[RULE_SUBRULE][i]
		parsedRules += parseRule(subRule, rule, "{}.{}".format(parentRuleIndex, i + 1) if parentRuleIndex else "{}".format(i + 1))

	return parsedRules


def parseRuleFile(filename='rule.json'):
	finalRules = []

	with open(filename) as json_data:
		rules = json.load(json_data)
		for rule in rules:
			finalRules += parseRule(rule, None, None)

	return finalRules

rules = parseRuleFile()

def submit(newTriggers):
	headers = {
		'Authorization': 'Basic Z3dhbmcrMjI0MzIzODUzODdAemVuZWZpdHMuY29tOmdQZE5WeEI5VyNtMjk+bS8=',
	}
	r = requests.get('https://www.zopim.com/api/v2/triggers', headers=headers)
	oldTriggers = r.json()
	for t in oldTriggers:
		print 'deleting', t['name']
		r = requests.delete('https://www.zopim.com/api/v2/triggers/{}'.format(t['name']), headers=headers)
		print r

	for t in newTriggers:
		print 'adding', t
		r = requests.post('https://www.zopim.com/api/v2/triggers', json=t, headers=headers)
		print r

rules = parseRuleFile()
submit(rules)
