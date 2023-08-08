# Useful queries

## general

```graphql
{
  general {
    kivaStats {
      amountFunded
      numBorrowers,
      numCountries,
      numLenders,
      repaymentRate,
      sectors {
        id,
        name
      }
    }
  }
}
```

## Get tags

```graphql
{
  lend {
    tag {
      id
      name
      vocabularyId
    }
  }
}

```

## Get loans

```graphql
enum LoanSearchStatusEnum {
  fundraising
  funded
  all
}
```

`loans(offset: Int = 0, limit: Int = 20, filters: LoanSearchFiltersInput = {distributionModel: both, status: fundraising}, queryString: String, sortBy: LoanSearchSortByEnum = popularity, promoOnly: BasketInput = null, promos: [Int] = null): LoanBasicCollection
`

```graphql
{
  lend {
    loans(offset: 0, limit: 2, filters: {distributionModel: both, status: all}, sortBy: newest) {
      totalCount
      values {
        activity {
          id
        }
        anonymizationLevel
        borrowerCount
        borrowers {
          id
        }
        dafEligible
        delinquent
        description
        descriptionInOriginalLanguage
        disbursalDate
        distributionModel
        endorser {
          id
        }
        fundraisingDate
        gender
        geocode {
          city
          state
          postalCode
          latitude
          longitude
        }
        hasCurrencyExchangeLossLenders
        id
        image {
          id
        }
        isMatchable
        inPfp
        loanAmount
        loanFundraisingInfo {
          fundedAmount
          isExpiringSoon
          reservedAmount
        }
        lenderRepaymentTerm
        matcherAccountId
        matcherName
        matchRatio
        matchingText
        name
        originalLanguage {
          id
        }
        minNoteSize
        paidAmount
        pfpMinLenders
        plannedExpirationDate
        previousLoanId
        raisedDate
        researchScore
        repaymentInterval
        sector {
          id
        }
        status
        tags
        terms {
          currencyFullName
          disbursalAmount
          disbursalDate
          flexibleFundraisingEnabled
        }
        use
        userProperties {
          favorited
          lentTo
          subscribed
          promoEligible
          amountInBasket
        }
        video {
          thumbnailImageId
          youtubeId
        }
        whySpecial
      }
    }
  }
}
```

## country

```graphql
{
  lend {
    countryFacets {
      country {
        name
        isoCode
        region
        ppp
        numLoansFundraising
        fundsLentInCountry
      },
      count
    }
  }
}

```


